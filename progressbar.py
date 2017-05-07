from multiprocessing import Lock
import sys


class ProgressBar:
    def __init__(self, total, data=0, name='down'):
        self.data = data
        self.total = total
        self.name = name
        self.lock = Lock()

    def log(self, count):
        with self.lock:
            self.data += count
            progress = self.data / self.total
            sys.stdout.write('\r' + self.name + '[+' + '+'*int(progress*30) + ']' +
                             ' | ' + '{0}'.format(str(progress*100)[:6] + '%'))
            sys.stdout.flush()
            if str(progress*100)[:3] == '100':
                print('\r')