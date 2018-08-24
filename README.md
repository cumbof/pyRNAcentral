# RNAcentral-data-retrieval-tool
Python tool to interact with the public RNAcentral APIs and automatically retrieve data.

It exploits the `rna` endpoint of the RNAcentral public APIs v1 to automatically retrieve sequences
(converted to the FASTA format) and the related metadata, starting with one or a list of RNAcentral IDs.

### Usage Examples

How to download the sequence and the related metadata of a single RNAcentral ID:
```
python rnacentral.py --id URS00005F3006
```

To simultaneously download a data from a list of RNAcentral IDs, switch the `--id` parameter with `--file` like below:
```
python rnacentral.py --fasta human_AND_rna_typelncRNA.list
```
The file specified under the `--file` parameter must contain one RNAcentral ID per line.

It is also possible to specify the path in which the generated FASTA and metadata files will be stored respectively 
with the parameters `--fastadir` and `--metadir`.
