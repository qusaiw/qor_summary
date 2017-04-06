import os
import compiler
some_list = ['uuu/i/t', 'uu/t/cells', 'uu/t/cells/']
for path in some_list:
    print path
    if os.path.basename(path) != 'cells':
        path = os.path.join(path, 'cells')
    print path
    print '******'
something = "average = (rise_delay + fall_delay) / 2"
