Check New Innovations Evaluations
====================

Vivek Sant (vsant@hcs.harvard.edu)

This program will check New Innovations for new grades and email/text new results.

settings.py should be populated with relevant login details.  [settings.py.sample](settings.py.sample) is a good template.

Designed to be run as a cronjob.  For example:

    */5 * * * * /fullpath/check.py

