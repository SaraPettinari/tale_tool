# TALE analysis #
TALE analysis implements a graphycal interface to handle robotic system data and analyze them with process mining techniques. This repository contains the tool for performing the process mining-based analysis to discover robots behavior via a DFG.

![Tale](/docs/imgs/logo.png)

Please refer to the methodology description for more details: [website](https://pros.unicam.it/tale/) and [paper](https://link.springer.com/chapter/10.1007/978-3-031-46587-1_7).

## Installation
```bash
git clone <repository_link>
```

## Requirements
- Python 3.8 or later

### Python dependecies installation

**Create a virtual environment**
```bash
python -m venv venv
```

**Activate the virtual environment**

_Windows_
```bash
myenv\Scripts\activate
```

_macOS and Linux_

```bash
source myenv/bin/activate
```

**Install dependencies**

```bash
pip install -r requirements.txt
```

## Run
```bash
python main.py  
```


## Example Scenario

### Event log uploading
![Uploading](/docs/imgs/log_upload.png)

### Event log filtering
This sidebar enables filtering the event log for resource name and/or case identifier.
![Filtering](/docs/imgs/filtering.png)

## DFG discovery
DFG of the multi-robot behavior enhanced with the possibility of highlighting incoming and outgoing edges.
![DFG](/docs/imgs/dfg.png)

## Enhancement
Enhancement interface showing the communication and spatial perspectives.
![Enhancement](/docs/imgs/enhancement.png)