#!/bin/sh

cd $1
rm -r __pycache__ meta.json
zip -r ../sonaveeb_integration.ankiaddon *

