# Instructions to Install and Setup

Download the [database](http://labrosa.ee.columbia.edu/millionsong/sites/default/files/lastfm/lastfm_similars.db)
Download the [track metadata](http://labrosa.ee.columbia.edu/millionsong/sites/default/files/AdditionalFiles/unique_tracks.txt)
Put them in the root level of the project

Create a conda environment to install all packages with:

  ``` conda create --name myenv --file conda-requirements.txt ```

Then activate the conda environment:

  ``` source activate myenv ```

To install Python-Louvain:

  ``` cd ./python-louvain-0.9 ```

  ``` python setup.py install ```

To Run the program:

  ```python script.py ```

Note to initially preprocess the db and create graph / communities it takes about 10-15 mins, be patient please.
After that the prompt runs in an infinite loop, *ctrl + c* to quit.

Each songs need to be given in the following format:
*Artist - Song;Artist2 - Song2;Artist3 - Song3*
Be careful of the spaces please.
