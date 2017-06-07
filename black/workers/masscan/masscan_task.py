""" Keeps class with the interfaces that are pulled by worker
to manager the launched instance of scan. """
import re
import signal
import socket
import threading
from time import sleep

import asyncio
from asyncio.subprocess import PIPE

from black.workers.common.async_task import AsyncTask
from black.workers.masscan.db_save import save_raw_output

class MasscanTask(AsyncTask):
    """ Major class for working with masscan """

    def __init__(self, task_id, target, params, project_uuid):
        AsyncTask.__init__(self, task_id, 'masscan', target, params, project_uuid)
        self.proc = None

        self.exit_code = None
        self.stdout = []
        self.stderr = []

        if type(self.target) == list:
            self.target = ",".join(self.target)
        print(self.target)

    async def start(self):
        """ Launch the task and readers of stdout, stderr """
        self.command = ['sudo', 'masscan'] + [self.target] + ['-oX', '-'] + self.params['program']

        try:
            self.proc = await asyncio.create_subprocess_exec(*self.command, stdout=PIPE, stderr=PIPE)
        except Exception as e:
            self.set_status("Aborted", progress=-1, text=str(e))
            print(e)

            raise e

        self.set_status("Working", progress=0)

        # Launch readers
        loop = asyncio.get_event_loop()
        loop.create_task(self.read_stdout())
        loop.create_task(self.read_stderr())

        # Launch status poller
        self.spawn_status_poller()

    def send_notification(self, command):
        """ Sends 'command' notification to the current process. """
        if command == 'pause':
            self.proc.send_signal(signal.SIGSTOP.value)  # SIGSTOP
        elif command == 'stop':
            self.proc.terminate()  # SIGTERM
        elif command == 'unpause':
            self.proc.send_signal(signal.SIGCONT.value)  # SIGCONT

    async def read_stdout(self):
        """ Read from stdout by chunks, store it in self.stdout """
        # If we know, that there will be some data, we read it
        if self.status == 'New' or self.status == 'Working':
            stdout_chunk = await self.proc.stdout.read(1024)
            self.stdout.append(stdout_chunk)

            # Create the task on reading the next chunk of data
            loop = asyncio.get_event_loop()
            loop.create_task(self.read_stdout())

        # If the task has finished, drain stdout
        elif self.status == 'Aborted' or self.status == 'Finished':
            try:
                # Try to read from stdout for quite some time
                stdout_chunk = await asyncio.wait_for(self.proc.stdout.read(), 0.5)

                # Wierd thing: while reading from the stdout of finished process,
                # b'' is read in a while loop, so we need to check.
                if len(stdout_chunk) == 0:
                    raise Exception("No data left")
                else:
                    self.stdout.append(stdout_chunk)
            except TimeoutError as _:
                pass
            except Exception as _:
                pass

    async def read_stderr(self):
        """ Similar to read_stdout """
        if self.status == 'New' or self.status == 'Working':
            stderr_chunk = await self.proc.stderr.read(1024)
            self.stderr.append(stderr_chunk)

            # Create the task on reading the next chunk of data
            loop = asyncio.get_event_loop()
            loop.create_task(self.read_stderr())

        # If the task has finished, drain stderr
        elif self.status == 'Aborted' or self.status == 'Finished':
            try:
                stderr_chunk = await asyncio.wait_for(self.proc.stderr.read(), 0.5)
                if len(stderr_chunk) == 0:
                    raise Exception("No data left")
                else:
                    self.stderr.append(stderr_chunk)
            except TimeoutError as _:
                pass
            except Exception as _:
                pass

    def spawn_status_poller(self):
        """ Spawn the thread that will poll for the progress """
        thread = threading.Thread(target=self.progress_poller)
        thread.start()

    def progress_poller(self):
        """ Gets the current progress and prints it
        TODO:
            * Should put result back to the queue (not yet and not rdy for this) """
        old_progress = 0
        old_found = None

        while self.status != "Finished" and self.status != "Aborted":
            if self.status == "New":
                print("[-] New")
            elif self.status == "Working":
                try:
                    data = str(self.stderr[-1])
                    if data:
                        percent = re.findall(r"([0-9]{1,3}\.[0-9]{1,3})%", data)
                        # time_left = re.findall(r"([0-9]{1,4}:[0-9]{1,2}:[0-9]{1,2})", data)
                        found = re.findall(r"found=([0-9]{0,5000})", data)

                        print("[-] Working {}%, {} found".format(
                            percent[0],
                            # time_left[0],
                            found[0]))

                        new_progress = int(percent[0].split('.')[0])
                        if new_progress != old_progress or old_found != found[0]:
                            old_progress = new_progress
                            self.set_status("Working", progress=new_progress)

                except Exception as exc:
                    print(exc)
                    pass

            sleep(1)
        print(self.status)

    async def wait_for_exit(self):
        """ Check if the process exited. If so,
        save stdout, stderr, exit_code and update the status. """
        print("Task started")
        exit_code = await self.proc.wait()
        self.exit_code = exit_code
        # The process has exited.
        print("The process finished OK")

        if self.exit_code == 0:
            try:
                self.save()
            except Exception as e:
                decoded_stderr = list(map(lambda x: x.decode('utf-8'), self.stderr))
                self.set_status("Aborted", progress=-1, text="".join(decoded_stderr))
            else:
                self.set_status("Finished", progress=100)
        else:
            decoded_stderr = list(map(lambda x: x.decode('utf-8'), self.stderr))
            self.set_status("Aborted", progress=-1, text="".join(decoded_stderr))

    def save(self):
        save_raw_output(
            self.task_id,
            self.stdout,
            self.project_uuid)
