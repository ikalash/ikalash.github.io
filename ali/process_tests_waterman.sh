
#!/bin/bash
bash execute_jupyter_nb_waterman.sh >& execute_jupyter_nb_waterman.out
bash concatenate_files_waterman.sh >& concatenate_files_waterman.out
cd waterman_nightly_data
rm -rf *out
python email_report.py >& email.out

