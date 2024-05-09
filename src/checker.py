##
# Gathers lpar information for individal managed_systems \ 
# and compares between "sister" systems to ensure consistency \
# across LR and OC
##

import paramiko
import logging
import socket
import numpy as np
import datetime, sys, os, pkgutil
import pandas as pd
import getpass
import argparse
import pathlib
from pathlib import Path

## ---- ERROR CODE CHEATSHEET ----
## Exit 10 - Dependency failure
## Exit 20 - File does not exist
## Exit 30 - User does not exist
## Exit 40 - Network issue

# Ignoring cryptographic errors for Paramiko + Checking for installation of Paramiko
import warnings 
warnings.filterwarnings(action='ignore',module='.*paramiko.*')
print("Dependencies in place - Continuing program.\n") if pkgutil.find_loader('paramiko') is not None else {logging.error("Paramiko is not installed - Exiting"), sys.exit(10)}
####

# Globals
remote_host="lpwrhmc1"
account=getpass.getuser()
pd.set_option('display.max_columns', None) #-> Print all Columns
pd.options.mode.chained_assignment = None
lr = "LR"
oc = "OC"
####

# Create output stagging directory under users path
output_dir = f"/home/{account}/IBM-lpar_consistency_output"
output_path = Path(output_dir)
output_path.mkdir(parents=False, exist_ok=True)


# Reset contents of output file
output_log = f"{output_dir}/run_output.log"
Path(output_log).touch()
output_log = output_log if os.path.isfile(output_log) else {logging.error(f"File {output_log} does not exist! - Creating Now"), Path(output_log).touch(), sys.exit(20)}

# Test if managed_systems file is writable to
managed_sys_list = f"{output_dir}/managed_systems.log"
Path(managed_sys_list).touch()
managed_sys_list = managed_sys_list if os.path.isfile(managed_sys_list) else {logging.error(f"File {managed_sys_list} does not exist! - Creating Now"), Path(managed_sys_list).touch(), sys.exit(20)}

# Setup some creds for Paramiko to use - NOTE, these strings will need to change depending on who is running this
# host_list_path = f"/home/{account}/lists/hmc.list"
rsa_key = "/home/" + account + "/.ssh/id_rsa"

# host_list_path = f"/home/{account}/lists/hmc.list" if (os.path.isfile(host_list_path)) else {logging.error("File does not exist!"), sys.exit(20)}
account=account if (os.path.isdir("/home/"+account)) else {logging.error("User does not exist!"), sys.exit(30)}
pkey=paramiko.RSAKey.from_private_key_file(rsa_key) if (os.path.isfile(rsa_key)) else {logging.error("File does not exist!"), sys.exit(20)}

# Test network status of a system - Method 1: ping
def test_ping(hostname)-> bool:
        host_connectivity = os.system("ping -c 1 -w 1 " + hostname)
        return True if host_connectivity == 0 else  False

# Test network status of a system - Method 2: socket to port 22
def test_connection(hostname, timeout=3):
  try:
    socket.setdefaulttimeout(timeout)
    socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((hostname, 22))
    return True
  except Exception as ex:
    return False

# Function for setting up connection to remote host and running command against host - \ 
# returns stdout / stderr if present
def run_command(server, account, pkey, command):
        host=socket.gethostbyname(server)
        # print("Hostname - " + server + "\n" + "Host Address - " +host)

        client=paramiko.SSHClient()
        policy=paramiko.AutoAddPolicy()
        client.set_missing_host_key_policy(policy)

        client.connect(host, username=account, pkey=pkey)
        _stdin, _stdout, _stderr = client.exec_command(str(command))
        _stdin.close()

        output=list()
        for line in _stdout:
             output.append(line.strip('\n'))
        error=_stderr.read().decode()
        error = None if error == "" else error

        # Debugging running command on remote host and getting error
        #print("Output: " + str(output), end="")
        #print("Error: " + str(error), end="\n\n")
        client.close()
        #return "No output - check error" if output == "" else { output }
        return output

# Creates dictionary using the "description" as the key, \
# and the values as the managed_systems that have the same description
def list_to_dict(newline_list: list)->dict:
    output_dict = dict()
    for line in newline_list:
          value = (line.split(" ")[0])
          key = (line.split(" ")[1])
          if key in output_dict:
               output_dict[key] += [value]
          else:
               output_dict[key] = [value]
    # print(output_dict)
    return output_dict


# This is the magic - creates "sister" pairs of managed_systems \
# that should contain like lpars on both LR/OC sides
def make_df_pars(raw_df: pd.DataFrame)->pd.DataFrame:
    output_df = pd.DataFrame()

    for lr, oc in raw_df.itertuples(index=False):
        if lr.split("-", 4)[4] != "LR":
            loc = raw_df[raw_df["LR"]==lr].index.values
            #print(df.loc[loc, "OC"].item(), lr)

            lr_side = raw_df.loc[loc, "OC"].item()
            oc_side = lr

            temp_df = pd.DataFrame([{"LR":lr_side, "OC":oc_side}])
            output_df = pd.concat([output_df, temp_df])

        #elif oc.split("-", 4)[4] != "OC":
            #print(oc)
        else:
            #print(lr, oc)
            temp_df = pd.DataFrame([{"LR":lr, "OC":oc}])
            output_df = pd.concat([output_df, temp_df])

    return output_df


class retrieve_lpar_info():
    switch = True

    logging.info("Network connection good - Continuing") if (test_connection(remote_host)) \
    else {logging.error("Network connection failure - Exiting"), sys.exit(40)}

    # Get list of frames + their descriptions - NOTE, if switch is True - 
    # will pull list from HMC via ssh and save to file. if False - it skips ssh and just reads from file
    if switch:
        frame_grouping_desc = run_command(remote_host, account, pkey, "lssyscfg -r sys -F name description | grep -iv decom | grep -iv mrx")
        # print(frame_grouping_desc)
        with open(managed_sys_list, "w") as m_systems_file:
            for item in frame_grouping_desc:
                m_systems_file.write(str(item)+"\n")
        #m_systems_file.write(str(frame_grouping_desc))
    
    # List -> Dict -> Dataframe (PULLS FROM FILE, IF NEEDING TO REFRESH FILE CONTENTS - RUN ABOVE WITH "switch = True")
    with open(managed_sys_list, "r") as m_systems_file:
        temp_list = []
        for line in m_systems_file.readlines():
            temp_list.append(line)

        dict_of_frames = list_to_dict(temp_list)


    df = pd.DataFrame.from_dict(dict_of_frames, orient='index', columns=['LR', 'OC'])

    # Clean up of dataframe
    df.sort_index(inplace=True)
    df = df.dropna()
    # Construct new dataframe with organization between LR / OC with sister pairs of managed_systems
    sister_pairs = make_df_pars(df)
    sister_pairs = sister_pairs.reset_index(drop=True)


    # lpar profile data points to be covered in dataframes
    column_names = ['lpar_id', 'lpar_name', 'name', 'min_mem', 'desired_mem', 'max_mem', 'proc_mode', 'min_proc_units', 'desired_proc_units', 
                    'max_proc_units', 'min_procs', 'desired_procs', 'max_procs', 'lpar_proc_compat_mode']
    
    prof_details = " "
    prof_details = prof_details.join(column_names)
    
    for lr_frame, oc_frame in sister_pairs.itertuples(index=False):
	# Create csv output stagging area for csv file outputs
        csv_output=f"/{output_dir}/output_{lr_frame}_{oc_frame}.csv"

        print(f"{lr_frame}  :  {oc_frame}")
        with open(output_log, "a") as logging_file:
            logging_file.write(f"{lr_frame} : {oc_frame}\n")

        gather_lpars_command_lr = f"lssyscfg -m {lr_frame} -r prof -F {prof_details} | grep -iv backup | sort -n"
        gather_lpars_command_oc = f"lssyscfg -m {oc_frame} -r prof -F {prof_details} | grep -iv backup | sort -n"
        
        lr_output = run_command(remote_host, account, pkey, gather_lpars_command_lr)
        oc_output = run_command(remote_host, account, pkey, gather_lpars_command_oc)

        lr_lpar_def = list()
        oc_lpar_def = list()

        for lpar in lr_output:
            lr_lpar_def.append(lpar.split(" "))

        for lpar in oc_output:
            oc_lpar_def.append(lpar.split(" "))


        lr_test_df = pd.DataFrame(lr_lpar_def)
        lr_test_df.columns = column_names
        lr_test_df.index = np.arange(1, len(lr_test_df) + 1)

        lr_lpar_names = lr_test_df[['lpar_id', 'lpar_name']]
        lr_lpar_names['lpar_id'] = lr_lpar_names['lpar_id'].astype("int64")

        oc_test_df = pd.DataFrame(oc_lpar_def)
        oc_test_df.columns = column_names
        oc_test_df.index = np.arange(1, len(oc_test_df) + 1)

        oc_lpar_names = oc_test_df[['lpar_id', 'lpar_name']]
        oc_lpar_names['lpar_id'] = oc_lpar_names['lpar_id'].astype("int64")

        # We dont care if they match, just say its good and continue on
        if lr_test_df.loc[:, lr_test_df.columns != 'lpar_name'].equals(oc_test_df.loc[:, oc_test_df.columns != 'lpar_name']):
            print("Matching = True", end="\n\n")
            print("-" * 200)
            with open(output_log, "a") as logging_file:
                logging_file.write("Matching = True\n\n")
                logging_file.write("-" * 200 + "\n")
        else:
            print("Matching = False", end="\n\n")

            # We do a merge on the two lr/oc dataframes to get left/right only values ->
            #  then we rename those to match the managed_system they were found on instead. So left only values = LR and right only values = OC
            merge_df = lr_test_df.loc[:, lr_test_df.columns != 'lpar_name'].merge(oc_test_df.loc[:, oc_test_df.columns != 'lpar_name'], indicator=True, how='outer')
            merge_df = merge_df.replace("left_only", lr_frame)
            merge_df = merge_df.replace("right_only", oc_frame)
            merge_df = merge_df.rename(columns={"_merge" : "FRAME"})


            # We collect the values that do not have "BOTH" in a col/row - this is the dataframe of lpars and their inconsistent values 
            diff_df = merge_df.loc[lambda x : x['FRAME'] != 'both']
            diff_df.lpar_id = pd.to_numeric(diff_df.lpar_id, errors='coerce')
            diff_df = diff_df.sort_values(by=["lpar_id"])

            diff_df['lpar_id'] = diff_df['lpar_id'].astype("int64")
            
            lr_final_frames = diff_df[diff_df['FRAME'].str.contains("LR")]
            oc_final_frames = diff_df[diff_df['FRAME'].str.contains("OC")]

            lr_out = pd.merge(lr_final_frames, lr_lpar_names, on="lpar_id")
            oc_out = pd.merge(oc_final_frames, oc_lpar_names, on="lpar_id")

            output = pd.concat([lr_out, oc_out])
            print(output)

            print(output.to_string(index=False), end='\n\n')
            print("-" * 200)
            with open(output_log, "a") as logging_file:
                logging_file.write(f"{output.to_string(index=False)}" + "\n\n")
                logging_file.write("-" * 200 + "\n")
            output.to_csv(csv_output)

# Run main
if __name__ == "__main__":
    run = retrieve_lpar_info()
