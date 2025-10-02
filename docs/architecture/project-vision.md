search the web to find can be utilized my usecase mcp server available.

MVP:
a simple script "job manager"
set path and job name
that pooling each 5 seconds ( configurable )

every 5 secords, the script checks a status of the job by name.
if it's not done yet, means remaining tasks exists,
and if no task runner for the job exists, invoke task runner (script claude code cli wrapper).
and manager set status of job to working. end of pooling process for job manager.

task runner fetch first remaining task from tasks of the job.
if found one, perform what task says.
if task runner deside it's bigger than single task, need more effort, different context, queue task(s) in need.
task runner only takes one task and end of task, kill task runner.

after task runner killed, pooling job manager find no task runner assigned for the job.
invoke task runner, runner fetch task, perform task, queue task in need, and killed.

keep performing this till every tasks done.
if no tasks to queue, manager set as done.

I can create script part, but if such task manager mcp server exists, want to utilize. oss :
OD:
