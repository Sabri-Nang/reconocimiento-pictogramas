"""Entrena MobileNetV3-Small ImageNet con train/validation; nunca carga test.csv."""
import argparse
import csv
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
import numpy as np
from PIL import Image
os.environ.setdefault("KERAS_HOME", str(Path(__file__).resolve().parents[1] / "models/.keras_cache"))
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]

def load_partition(name, classes, size):
    with (ROOT / f"data/splits/{name}.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise ValueError(f"Partición vacía: {name}")
    images, labels = [], []
    for row in rows:
        index = int(row["class_index"])
        if index < 0 or index >= len(classes) or classes[index] != row["class_id"]:
            raise ValueError("Índice de clase inconsistente")
        with Image.open(ROOT / row["processed_path"]) as im:
            if im.mode != "RGB" or im.size != size:
                raise ValueError(f"Imagen sin preparar: {row['processed_path']}")
            images.append(np.asarray(im, dtype=np.uint8))
        labels.append(index)
    if set(labels) != set(range(len(classes))):
        raise ValueError(f"Faltan clases en {name}")
    return np.stack(images), np.asarray(labels), rows

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--fine-tune-epochs", type=int, default=10)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1 or args.fine_tune_epochs < 0:
        parser.error("epochs y batch-size deben ser positivos")
    config = json.loads((ROOT / "config/project.json").read_text(encoding="utf-8"))
    classes = [c["id"] for c in config["classes"]]
    size = (config["image"]["width"], config["image"]["height"])
    seed = config["random_seed"]
    tf.keras.utils.set_random_seed(seed)
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    x_train, y_train, train_rows = load_partition("train", classes, size)
    x_val, y_val, val_rows = load_partition("validation", classes, size)
    for field in ["session_id", "raw_path", "processed_path", "sha256"]:
        if {r[field] for r in train_rows} & {r[field] for r in val_rows}:
            raise ValueError(f"Fuga entre train y validation: {field}")
    plan = json.loads((ROOT / "config/dataset_partitions.json").read_text(encoding="utf-8"))
    for split, rows in [("train", train_rows), ("validation", val_rows)]:
        if {r["session_id"] for r in rows} != set(plan["sessions"][split]):
            raise ValueError(f"Sesiones inconsistentes: {split}")
    run = datetime.now(timezone.utc).strftime("mobilenet_%Y%m%d_%H%M%S")
    model_dir = ROOT / "models" / run
    report_dir = ROOT / "reports" / run
    model_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    layers = tf.keras.layers
    base = tf.keras.applications.MobileNetV3Small(
        input_shape=(size[1],size[0],3), include_top=False,
        weights="imagenet", include_preprocessing=True, pooling="avg")
    base.trainable = False
    inputs = layers.Input(shape=(size[1],size[0],3))
    augmented = layers.RandomRotation(0.04, seed=seed)(inputs)
    augmented = layers.RandomTranslation(0.05,0.05, seed=seed+1)(augmented)
    augmented = layers.RandomZoom(0.1, seed=seed+2)(augmented)
    features = base(augmented, training=False)
    features = layers.Dropout(0.3,seed=seed)(features)
    outputs = layers.Dense(len(classes),activation="softmax")(features)
    model = tf.keras.Model(inputs, outputs, name="mobilenet_pilot")
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    with (report_dir / "architecture.txt").open("w",encoding="utf-8") as f:
        model.summary(print_fn=lambda line:f.write(line+"\n"))
    dataset_options=tf.data.Options()
    dataset_options.threading.private_threadpool_size=2
    train=tf.data.Dataset.from_tensor_slices((x_train,y_train)).shuffle(len(y_train),seed=seed).batch(args.batch_size).with_options(dataset_options).prefetch(1)
    validation=tf.data.Dataset.from_tensor_slices((x_val,y_val)).batch(args.batch_size).with_options(dataset_options).prefetch(1)
    checkpoint=model_dir / "best.keras"
    callbacks=[tf.keras.callbacks.ModelCheckpoint(str(checkpoint),monitor="val_loss",save_best_only=True), tf.keras.callbacks.EarlyStopping(monitor="val_loss",patience=6,restore_best_weights=True),tf.keras.callbacks.CSVLogger(str(report_dir / "history.csv"))]
    print(f"Experimento {run}: {len(y_train)} train, {len(y_val)} validation; test no utilizado.",flush=True)
    start = time.perf_counter()
    first=model.fit(train,validation_data=validation,epochs=args.epochs,callbacks=callbacks,verbose=2)
    histories = {key:list(value) for key,value in first.history.items()}
    head_epochs = len(histories["loss"])
    if args.fine_tune_epochs:
        model=tf.keras.models.load_model(checkpoint)
        base = next(layer for layer in model.layers if isinstance(layer, tf.keras.Model))
        base.trainable = True
        for layer in base.layers[:-30]:
            layer.trainable = False
        for layer in base.layers:
            if isinstance(layer, layers.BatchNormalization):
                layer.trainable = False
        model.compile(optimizer=tf.keras.optimizers.Adam(1e-5),loss="sparse_categorical_crossentropy",metrics=["accuracy"])
        fine_callbacks=[tf.keras.callbacks.ModelCheckpoint(str(checkpoint),monitor="val_loss",save_best_only=True,initial_value_threshold=min(histories["val_loss"])),tf.keras.callbacks.EarlyStopping(monitor="val_loss",patience=4),tf.keras.callbacks.CSVLogger(str(report_dir / "history_fine_tune.csv"))]
        print("Ajuste fino: últimas 30 capas, BatchNormalization congelada, lr=1e-5.",flush=True)
        fine=model.fit(train,validation_data=validation,epochs=args.fine_tune_epochs,callbacks=fine_callbacks,verbose=2)
        for key,value in fine.history.items():
            histories[key].extend(value)
    elapsed = time.perf_counter()-start
    class History:
        history=histories
    history=History()
    model=tf.keras.models.load_model(checkpoint)
    probabilities=model.predict(validation,verbose=0)
    predicted=probabilities.argmax(axis=1)
    loss,accuracy=model.evaluate(validation,verbose=0)
    report=classification_report(y_val,predicted,labels=list(range(len(classes))),target_names=classes,output_dict=True,zero_division=0)
    cm=confusion_matrix(y_val,predicted,labels=list(range(len(classes))))
    metrics=dict(run=run,partition="validation",validation_accuracy=float(accuracy),validation_loss=float(loss),best_epoch=int(np.argmin(history.history["val_loss"])+1),epochs_completed=len(history.history["loss"]),classification_report=report,confusion_matrix=cm.tolist(),test_evaluated=False,threshold_calibrated=False, training_seconds=elapsed, head_epochs=head_epochs)
    (report_dir / "metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8")
    with (report_dir / "predictions_validation.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.writer(f);writer.writerow(["raw_path","true_class","predicted_class","confidence"])
        for row,pred,prob in zip(val_rows,predicted,probabilities):
            writer.writerow([row["raw_path"],row["class_id"],classes[int(pred)],float(prob.max())])
    experiment=dict(run=run,seed=seed,classes=classes,image_size=list(size),epochs=args.epochs,batch_size=args.batch_size,tensorflow=tf.__version__,input_range="uint8 0..255; MobileNetV3 incluye Rescaling a -1..1", pretrained_weights="ImageNet", fine_tune_epochs=args.fine_tune_epochs,augmentation="rotation 0.04, translation 0.05, zoom 0.1; solo entrenamiento",selection="mínimo val_loss; early stopping patience 6",manifests_sha256={name:hashlib.sha256((ROOT/f"data/splits/{name}.csv").read_bytes()).hexdigest() for name in ["train","validation"]})
    (model_dir / "experiment.json").write_text(json.dumps(experiment,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,metric,label in zip(axes,["loss","accuracy"],["Pérdida","Exactitud (proporción)"]):
        for key,title in [(metric,"Entrenamiento"),("val_"+metric,"Validación s006")]:
            ax.plot(range(1,len(history.history[key])+1),history.history[key],label=title)
        ax.set(xlabel="Época",ylabel=label,title=label);ax.legend()
    fig.tight_layout();fig.savefig(report_dir/"learning_curves.png",dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(6,5));ax.imshow(cm,cmap="Blues")
    ax.set(xticks=range(len(classes)),yticks=range(len(classes)),xticklabels=classes,yticklabels=classes,xlabel="Clase predicha",ylabel="Clase real",title="Validación s006: cantidad de imágenes")
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j,i,str(cm[i,j]),ha="center",va="center",color="white" if cm[i,j]>cm.max()/2 else "black")
    fig.tight_layout();fig.savefig(report_dir/"confusion_validation.png",dpi=150);plt.close(fig)
    print(json.dumps({"run":run,"validation_accuracy":float(accuracy),"best_epoch":metrics["best_epoch"],"model":str(checkpoint),"reports":str(report_dir)},indent=2),flush=True)

if __name__ == "__main__":
    main()
