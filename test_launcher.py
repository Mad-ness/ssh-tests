#!/usr/bin/env python
#
# Changelog: 25/12/2018
#  - rewritten some functions
#  - option --task-from-file renamed to --task
#  - options --var_file and --task accepts many files after it without a need
#    to have the option name before each file
#  - added option --debug. It shows stderr and stdout from a remote host
#  - removed a lot of unneded code
#  - implemented support of tags. Option --tag. Tasks with at least one specified tag will run.
#    By default, no tags are used.
#  - added version information. Option --version
# Update: 25/12/2018
#  - fixed wrong not running tasks when no tags specified
#

import os, sys
import paramiko
import socket
import argparse
from jinja2 import Template
import yaml
import time


### VERSIONING 
# Update it with significant changes like adding new functionality
version_major = 1
# Update it with minor changes, for example, improved some algorithm
version_minor = 0
# Update it when a fix is made
version_patch = 1


class RetCode:
  Pass = 0
  Fail = 1
  Warn = 2


def render_template(plain_text, vars):
  """
  Renders a plain text doing replacement of passed vars, if any
  """
  t = Template(plain_text)
  content = t.render(vars)
  return content


def remote_executing(script, debug, **kwargs):
  """
  Connects to a remote server with provided credentials and run provided script.
  Accepted arguments:
    host - a remote host, hostname or IP address
    port - a ssh port
    username, password - credentials used for connecting
    script - a script that is being executing remotely
    returnCodes - return codes that taken from task.metadata.returnCodes
  """
  result = None
  host, port, username, password = None, 22, None, None
  for key, value in kwargs.items():
    if key == 'host': 
      host = value; 
      continue
    if key == 'port': 
      port = value; 
      continue
    if key == 'username': 
      username = value; 
      continue
    if key == 'password':
      password = value
      continue
    if key == 'returnCodes':
      returnCodes = value
      continue

  # print(host, username, password)
  if host is None or username is None or password is None:
    print("Variables host, username, and password must be passed")
    sys.exit(1)
    return RetCode.Fail

  try:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    try:
      client.connect(hostname=host, port=port, username=username, password=password, timeout=5.0)
    except ( paramiko.SSHException, socket.error ) as exc:
      client.close()
      return ( RetCode.Fail, "ConnErr %s while " % exc )
    except paramiko.AuthenticationException as exc:
      client.close()
      return ( RetCode.Fail, "AuthErr %s while " % exc )
      

    channel = client.get_transport().open_session()
    channel.exec_command(script)
    channel.shutdown_write()
    stdout = channel.makefile().read()
    stderr = channel.makefile_stderr().readlines()
    if debug:
      print("Stderr:")
      print('\n'.join(stderr))
      print("Stdout:")
      print(stdout)
    exit_code = channel.recv_exit_status()
    result = exit_code
    channel.close()
  finally:
    client.close()
  if exit_code == int(returnCodes['pass']):
    return (RetCode.Pass, "")
  elif exit_code == int(returnCodes['warn']):
    return (RetCode.Warn, "")
  else:
    return (RetCode.Fail, "")


def file_loader_from_disk(filename):
  result = None
  try:
    result = open(filename, 'r').read()
  except IOError as exc:
    print(exc.msg);
  return result;


def text_to_yaml(buffer):
  """
  Converts buffer to yaml format
  """ 
  return yaml.load(buffer)

def yaml_loader_from_disk(filename):
  """
  Loads a task in YAML format from a file on a disk
  """
  result = yaml.load(file_loader_from_disk(filename))
  return result


def merge_dicts(dict1, dict2):
  """
  Merges two dictionaries into a single one and returns it.
  If the same variables are met in both dictionaries
  dict1 takes a precedence over dict2
  """
  z = dict1.copy()
  z.update(dict2)
  return z


def show_verinfo():
  """
  Version information
  """
  print("{ver_major}.{ver_minor}.{ver_patch}".format(
    ver_major = version_major,
    ver_minor = version_minor,
    ver_patch = version_patch,
  ))
  pass

def menu_parsing():
  """
  It parses passed arguments and calls neccessary functions
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--vars-file", required=False, help="Load variables from file on a disk", nargs='*')
  parser.add_argument("-e", "--env-var", action='append', required=False, nargs='*', help="Passing arguments to a task as var=value. Might be used many times")
  parser.add_argument("-t", "--task", required=False, nargs='*', help="A path to a task in YAML format. Multiple files allowed")
  parser.add_argument("--tag", required=False, default=None, help="Select only the tasks with provided tag(s). Use a comma-separator to specify multiple tags")
  parser.add_argument("-o", "--output", required=False, default=None, help="Print a result message in specified log file")
  parser.add_argument("-d", "--debug", required=False, default=False, action='store_true', help="Debug output")
  parser.add_argument("--version", action='store_true', default=False, required=False, help="Print version information and exit")
 
  args = parser.parse_args()

  if args.version:
    show_verinfo()
    sys.exit(0)

  vars_from_files = dict()
  task_vars = dict()
 
  # Load variables from files which specified with -v
  if args.vars_file is not None:
    for var_file in args.vars_file:
      new_vars = yaml_loader_from_disk(var_file)
      task_vars = merge_dicts(new_vars, task_vars)
  # if there vars passed as -e 
  # append them all to all_vars dictionary
  if args.env_var is not None:
    for pair in args.env_var:
      key, value = pair[0].split('=', 1)
      task_vars[key] = value

  # print(args.task)
  # print(args.vars_file)
  exit_code = 0
  if args.task is not None:
    for task_file in args.task:
      # print("Processing file", task_file)
      task_text = file_loader_from_disk(task_file)
      if len(task_text) > 0:
        task_content = text_to_yaml(render_template(task_text, task_vars))
        task_vars['returnCodes'] = task_content['metadata']['returnCodes']
        # If --tag is specified
        if args.tag is not None:
          task_tags = task_content['metadata'].get('tags')
          if task_tags is not None:
            if type(task_tags) == str and len(task_tags): 
              task_tags = [ x.strip() for x in task_tags.split(',') ]
            selected_tags = [ x.strip() for x in args.tag.split(',') ]
  
            # print("Tags", task_tags, selected_tags)
      
            if selected_tags is not None and not len([ tag for tag in selected_tags if tag in task_tags ]): # selected_tags not in task_tags:
              # skip tasks that do not have requsted tag
              continue; 
            
        retCode, err_msg = remote_executing(script=task_content['script'], debug=args.debug, **task_vars)
        # print( err_msg, retCode )
        if retCode == RetCode.Fail:
          exit_code += 1
        print_output( task_content['metadata']['title'], err_msg, retCode, logtofile=args.output )
  else:
    print("No one task is specified")
    exit_code = 1
    pass
  sys.exit(exit_code) 

def print_output( title, errmsg, retCode, logtofile ):
  """
  Formatted output
  """
  status = "FAIL"
  if retCode == RetCode.Warn:
    status = "WARN"
  elif retCode == RetCode.Pass:
    status = " OK "
  msg = "[{status}] {errmsg}{title}".format(
    status = status,
    errmsg = errmsg,
    title = title,
  )
  print( msg )
  if logtofile is not None:
    try:
      open(logtofile, 'a+').write(msg + "\n")
    except:
      pass


if __name__ == "__main__": 
  menu_parsing()

