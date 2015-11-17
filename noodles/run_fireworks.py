

__all__ = ['run_fireworks', 'NoodleTask']

"""
Notes:
 *
"""

#================> Python Standard  and third-party <==========

from importlib import import_module
import sys
## ================ FireWorks modules  ==================
from fireworks                          import FireTaskBase,  Firework, FWorker, PyTask, ScriptTask, Workflow
from fireworks.queue.queue_launcher     import rapidfire, launch_rocket_to_queue
from fireworks.utilities.fw_serializers import FWSerializable
from fireworks.user_objects.queue_adapters.common_adapter import CommonAdapter

#=================> QMWorkflows module <=================
from qmworks.mongoConfig.remoteMongo import remoteLpad


#==================> Internal modules <==========
from .datamodel import *

#====================<>===============================

#TODO: Remote Queue
def run_fireworks(workflow, remote_db = None,  queue_type = 'SLURM', walltime ='00:15:00', cpus_per_task = 1, task_per_node = 1, ntasks = 1, maxjobs_queue = 10):
    """
    Returns the result of evaluting the worflow using the `Offline <https://pythonhosted.org/FireWorks/offline_tutorial.html?highlight=offline>` mode of fireworks.
 
    :param workflow:  Workflow to compute
    :type  workflow:  namedTuple |Workflow| or |PromisedObject| 
    :param remote_host: Remote platform to run the calculations
    :type  remote_host: string
    """


     ## FireWorks Configuration
    if remote_db:
        launchpad, handlerPort = remoteLpad(remote_db)
    else:
        launchpad = LaunchPad()
    launchpad.reset('', require_password=False)
    
    #Queue  Configuration
    fworker      = FWorker(name = "Noodles_worker" )
    queueadapter = create_qadapter(queue_type, walltime, cpus_per_task, task_per_node)
    
    #Create WorkFlows
    fireworks_WF     = create_tasks(workflow)
    launchpad.add_wf(fireworks_WF) 

    
    rapidfire(launchpad, fworker, queueadapter, maxjobs_block,
              nlaunches = "infinite", reserve = "True", njobs_queue = maxjobs_queue )

    if remote_db:
        handlerPort.kill()    # close connections    

    

#====================<>===============================
def create_tasks(wf):
    """
    Translates the workflows generated by the Engine infrasctructure to a Fireworks Workflow.
    :param wf: Workflow container
    :type wf:    PromisedObject | Workflow
    :returns wf: Fireworks Workflow
    """

    workflow = get_workflow(wf)
    
    root_ref, nodes, links = workflow

    connections = fireworks_connections(links)
    fireworks   = []
    for k in nodes.keys():
        n= create_noodle_task(k,nodes[k],links)
        fireworks.append(n)
        
    return WorkFlow(fireworks, connections)

def create_noodle_task(key, node, links):
    """
    Calculates the expression inside the node using the bound arguments. The variables
    corresponding to workflows are lookup from the database. Also, the node evaluation
    result is stored in the database.
    :param key: Unique node identifier  
    :param key: int
    :param node: Closure to execute remotely
    :type node: |FunctionNode|
    :param links: Dependencies between nodes
    :type  links: Dict
    """

    fun_node   = node.node
    fun_module = fun_node.module
    fun_name   = fun_node.name
    fun_qual   = fun_module + '.' + fun_name
     
    #variable representing the result of computing this node, store in the db
    var_res      = 'var_{}'.format(key)

    # 
    args, kwargs = fireworks_dependencies(key,node,links)
    task         = PyTask(fun_qual, args = args, kwargs = kwargs, stored_data_varname = var_res) 

    return Firework(task, spec={"_pass_job_info": True}, fw_id = key)

def fireworks_dependencies(key,node,links):
    """
    :param key: Unique node identifier  
    :param key: int
    :param node: Closure to execute remotely
    :type node: |FunctionNode|
    :param links: Dependencies between nodes
    :type  links: Dict
    """
    var_names = node.bound_args.signature.parameters.keys()

    return args, kwargs 


def fireworks_connections(links):
    """
    Using the Noodles depencies returns a dictionary of Depencies for Fireworks.
    :param links: Dependencies between nodes
    :type  links: Dict
    """
    ds = {}
    for k in links.keys():
        ds[k] = get_children[k]

    return ds

def get_children(set_vars):
    """
    :param set_vars: set of pair (node_target, var_to_calculate) 
    :param set_vars: Set
    """
    return  [k for k,_var in set_vars]
        
    



#====================<>===============================
    
def create_qadapter(queue_type, walltime, cpus_per_task, task_per_node):
    
    return CommonAdapter(q_type=queue_type.upper(), qname= "Noodles_queue",
                         rocket_launch = "rlaunch singleshot --offline", ntasks = 1,
                         cpus_per_task = cpus_per_task, walltime = walltime, queue = None,
                         account = None, job_name = "Workflow", pre_rocket = None,
                         post_rocket  = None
           )


