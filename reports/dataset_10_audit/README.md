# Auditoría del dataset de diez clases

Se auditaron 1800 conocidas y 250 desconocidas de s001-s006. Las 2050 filas de
metadata coinciden con las capturas; todas son legibles, 3072x3072 y no se
hallaron duplicados exactos. Ver integrity.json e inventory.csv.

Se revisaron 14 hojas de contacto; no se detectaron etiquetas claramente
incorrectas. ayuda_s001_0005.jpg y ayuda_s001_0011.jpg presentan desenfoque,
confirmado al inspeccionar originales. Se conservan y se recomienda revisar
su recaptura antes de fijar las rondas. Las tomas lejanas reducen el detalle
a 128x128. La revisión por miniaturas no certifica nitidez de todos los originales.
No se buscaron duplicados aproximados ni se certificó independencia física
de captura únicamente a partir de los nombres de sesión.

Se verificaron 1800 PNG RGB 128x128 y sus manifiestos. train.csv (1500) y
validation.csv (300) son referencias; development.csv (1800) reúne s001-s006
para futuras rondas. test.csv está vacío y s007 permanece reservada.
Los desconocidos no se incorporan a las diez clases ni se particionan aquí.
No se ejecutaron nuevos entrenamientos ni se cambiaron los modelos del piloto.
Los manifiestos anteriores están respaldados en reports/dataset_preparation_backups/.
