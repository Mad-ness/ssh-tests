#!/usr/bin/env python

import os, sys
import paramiko
import socket
import argparse
from jinja2 import Template
import yaml
import time


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

  if host == None or username == None or password == None:
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


def menu_parsing():
  """
  It parses passed arguments and calls neccessary functions
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--vars-file", required=False, help="Load variables from file on a disk", action='append', nargs=1)
  parser.add_argument("-e", "--env-var", action='append', required=False, nargs=1, help="Passing arguments to a task as var=value. Might be used many times")
  parser.add_argument("-t", "--task-from-file", required=True, nargs='*', help="A path to a task in YAML format. Multiple files allowed")
  parser.add_argument("-d", "--debug", required=False, default=False, action='store_true', help="Debug output")
 
  args = parser.parse_args()

  vars_from_files = dict()
  task_vars = dict()
  # Load variables from files which specified with -v
  if args.vars_file is not None:
    for var_file in args.vars_file:
      new_vars = yaml_loader_from_disk(var_file[0])
      task_vars = merge_dicts(new_vars, task_vars)
  # if there vars passed as -e 
  # append them all to all_vars dictionary
  if args.env_var is not None:
    for pair in args.env_var:
      key, value = pair[0].split('=', 1)
      task_vars[key] = value

  for task_file in args.task_from_file:
    task_text = str()
    with open(task_file, 'r') as task_fd:
      task_text = task_fd.read()
    if len(task_text) > 0:
      #print(task_vars)
      task_content = text_to_yaml(render_template(task_text, task_vars))
      print(task_content)
      task_vars['returnCodes'] = task_content['metadata']['returnCodes']
      print(task_vars)
      retCode, err_msg = remote_executing(script=task_content['script'], debug=args.debug, **task_vars)
      print( err_msg, retCode )
    pass
  pass


def loader2():
  """
  A wrapper of all things into one place
  """
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--vars-file", required=False, help="Load variables from file on a disk")
  parser.add_argument("-e", "--env-var", action='append', required=False, nargs=1, help="Passing arguments to a task as var=value. Might be used many times")
  parser.add_argument("-t", "--task-from-file", required=True, nargs='*', help="A path to a task in YAML format. Multiple files allowed")
  parser.add_argument("-d", "--debug", required=False, default=False, action='store_true', help="Debug output")
 
  args = parser.parse_args()

  start_time = time.time()
 
  task_counter = 0
  for task_in_file in args.task_from_file:
    task_counter += 1
  
    runtime_vars = dict()
    vars_content = dict()

    if args.vars_file is not None:
      vars_from_file = yaml_loader_from_disk(args.vars_file)
      vars_content = merge_dicts(runtime_vars, vars_from_file)
  
    if args.env_var is not None:
      for pair in args.env_var:
        key, value = pair[0].split('=', 1)
        vars_content[key] = value


    task_buffer = file_loader_from_disk(task_in_file)
    rendered_buffere= render_template(task_buffer, vars_content)
    task_content = text_to_yaml(rendered_buffer)

    retCode, metadata, err_msg, metadata = execute_task(task_content, vars_content, debug=args.debug)
    status = ' OK '
    if retCode == RetCode.Fail:
      status = 'FAIL'
    elif retCode == RetCode.Warn:
      status = 'WARN'
    output_message = "[{status}] {errmsg}{title}".format(
        t_counter = task_counter,
        errmsg = err_msg,
        all_tasks = len(args.task_from_file),
        title = metadata['title'],
        status = status,
      )
    print(output_message)
  pass


def cli_handler(listfiles_tasks, listfiles_vars, dict_vars, debug):
  """
  It accepts a list of arguments and run further procedures
  """

  def read_file(fname, raise_error_if_error=False):
    """
    Gets a content of file fname
    """
    result = open(fname, 'r').read()
    return result
  

  all_vars = dict()
  for fname in listfiles_vars:
    varfile_content = yaml.dump(read_file(fname))
    all_vars = merge_dicts(all_vars, varfile_content)

  for key, value in dict_vars:
    all_vars[key] = value


  for fname in listfiles_tasks:
    taskfile_yaml = yaml.dump(render_template(read_file(fname), all_vars))



  pass


def ta2sk_loader(task, task_vars, debug):
  """ 
  Buffer accepted as plain text and performing needed processing of 
  data in it
  param buffer is plain text of a task loaded from file or whatever else
  param vars is a dictionary of variables
  """
  # task_content = text_to_yaml(render_template(buffer, task_vars))
  retCode, metadata, err_msg = execute_task(task, task_vars, debug=debug) 
  status = ' OK '
  if retCode == RetCode.Fail:
    status = 'FAIL'
  elif retCode == RetCode.Warn:
    status = 'WARN'

#   output_message = "[{status}] {errmsg}{title}".format(
#     errmsg = err_msg,
#     title = metadata['title'],
#     status = status,
#   )
  return ( err_msg, status )


def e2xecute_task(task_content, vars_content, debug):
  """
  Executes a single task. A complete task should be loaded to
  raw_task_content buffer. In vars_in_yaml are passed variables, if needed.
  """
  retCode = 255
  metadata = dict()
  if task_content != None:
    print("Task content", task_content)
    print("Task vars", vars_content)
    # metadata = yaml.load(render_template(yaml.dump(task_content['metadata'], default_flow_style=False), vars_content))
    vars_content['returnCodes'] = metadata['returnCodes']

    # print(vars_content)
    script = render_template(task_content['script'], vars_content)
    retCode, err_msg = remote_executing(script=script, debug=debug, **vars_content)
  else:
    err_msg = "Task content is empty"
  return ( retCode, err_msg ) 
  


if __name__ == "__main__": 
  menu_parsing()

