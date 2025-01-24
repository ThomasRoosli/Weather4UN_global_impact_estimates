# Weather4UN_global_impact_estimates
The WMO Coordination Mechanism (WCM) aims to provide relevant weather and climate information as well as situation awareness to humanitarian agencies, supporting anticipatory action. The Federal Office for Meteorology and Climatology MeteoSwiss actively contributes to the WCM through its [Weather4UN pilot project](https://www.researchgate.net/publication/359467163_Stepping_Up_Support_to_the_UN_and_Humanitarian_Partners_for_Anticipatory_Action). In the Weather4UN pilot project the impact modelling framework [CLIMADA](https://climada-python.readthedocs.io/en/stable/) was used to calculate global impact estimates of tropical cyclones. This repository should document the approach chosen during the project work.

Follow this steps to be able to run the Jupyter Notebook:
- Create a conda/mamba environment with climada_python v4.1.1 and climada_petals v4.1.0 installed. Do this by running "mamba install -c conda-forge climada-petals=4.1.0" (it is always recommended to use a new environment.
- Install the pydantic package and the jupyter package additionally "mamba install pydantic" and "mamba install jupyter"
- Clone this repository to the folder where Climada is installed: "pip install -e /path/to/Weather4UN_global_impact_estimates"
