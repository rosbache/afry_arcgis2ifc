#Convert ArcGIS Shape file to IFC file

Input: FKB data in ArcGIS Shape format 
Output: ifc file with cube for points, pipe for lines and volume for polygon geometries. 
All attributes are added to the element in the ifc file. 
Objects are colored based on the FKB Screen values used in Norgeskart.no 
Source: https://register.geonorge.no/data/documents/tegneregler_N5%20Kartdata_spesifikasjon-skjermkartografi-20091102_.pdf 

## How to run
Text

```
python gis2bim.py -i "C:\Users\HTO334\OneDrive - AFRY\Documents\GitHub\afry_arcgis2ifc" -o "Samferdsel.ifc" -s "fkb-vei_style.json" 
```

## Examples
3D-buildins with properties extraced from 2d footprint
![image](https://github.com/user-attachments/assets/e5f9d878-d473-4837-bd97-a4ca36258d7a)

From SOSI-file in the software SOSI-vis:
![sosi-vis](https://github.com/user-attachments/assets/ed25147d-812b-44f8-960d-d46a39742adf)

Converted to ESRI ArcGIS shape-file (not in this software) and displayed in QGIS (no styling done):
![qgis](https://github.com/user-attachments/assets/7ffaa007-d14b-487f-9408-03bb2f3ea39e)

Converted to IFC-file using this library and displaying two ifc files in BIMvision (buildings and road surface for road and biking paths):
![bimvision](https://github.com/user-attachments/assets/166476f5-0380-4ca7-a2cc-a628d64948a5)

Compare with all data publicly available in norgeskart.no:
![norgeskart](https://github.com/user-attachments/assets/d9075437-becc-41ff-9ebc-c1e8d19e89c9)

Another example in BIMvision with buildings and cadastre lines from Matrikkelen:
![2025-02-19 14_25_26-IFC Viewer](https://github.com/user-attachments/assets/1385ea0c-f936-4a75-afe3-47495a2407c1)
