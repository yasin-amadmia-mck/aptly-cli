import subprocess
import sys
import getopt
import datetime, time
from pprint import pprint as pp


ARGS={}
APTLY_EXEC='/usr/bin/aptly'
MIRRORS=[]
PUBLISHED=[]
SNAPSHOTS_MAP={}
TIMESTAMP = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')

def run_command(command):
    print "Running: {}".format(command)
    p=subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err=p.communicate()
    if p.returncode != 0 :
        raise BaseException("{}".format(err or out))
    return out.split()

def create_snapshots_map():
    global SNAPSHOTS_MAP
    SNAPSHOTS_MAP={}
    SNAPSHOTS=run_command(APTLY_EXEC+" snapshot list -raw")
    MIRRORS=run_command(APTLY_EXEC+" mirror list -raw")
    TIME_STAMPS={ snapshot.split('_')[-1] for snapshot in SNAPSHOTS }
    DISTS= { ''.join(snapshot.split('_')[1]) for snapshot in SNAPSHOTS }
    for timestamp in TIME_STAMPS:
        TEMP_MAP={}
        snapshots=[snap for snap in SNAPSHOTS if timestamp == snap.split('_')[-1]]
        for distribution in DISTS:
            common_snaps=[snapshot for snapshot in snapshots if snapshot.split('_')[1] == distribution]
            if len(common_snaps) > 0:
                TEMP_MAP.update({distribution:common_snaps})
        SNAPSHOTS_MAP.update({timestamp:TEMP_MAP})
    pp(SNAPSHOTS_MAP)


def aptly_create_mirrors():
    for component in ARGS['COMPONENTS']:
        if ARGS['PUBLISH']+'_'+ARGS['DIST']+'_'+component not in MIRRORS:
            run_command(APTLY_EXEC+" mirror create -architectures="+ARGS['ARCHS']+" "+ARGS['PUBLISH']+'_'+ARGS['DIST']+'_'+component+' '+ARGS['URL']+' '+ARGS['DIST']+' '+component)
        else:
            print "Not creating mirror: {} as mirror already present".format(ARGS['PUBLISH']+'_'+ARGS['DIST']+'_'+component)
        

def aptly_update_mirrors():
    for component in ARGS['COMPONENTS']:
        run_command(APTLY_EXEC+" mirror update "+ARGS['PUBLISH']+'_'+ARGS['DIST']+'_'+component)
    

def aptly_create_snapshots():
    for component in ARGS['COMPONENTS']:
        run_command(APTLY_EXEC+" snapshot create "+ARGS['PUBLISH']+'_'+ARGS['DIST']+'_'+component+'_'+TIMESTAMP+' from mirror '+ARGS['PUBLISH']+'_'+ARGS['DIST']+'_'+component)


def aptly_publish(timestamp):
    create_snapshots_map()
    for item in SNAPSHOTS_MAP[timestamp].items():
        if item[0] == ARGS['DIST']:
            temp_s1=""
            temp_s2=","*(len(item[1])-1)
            for snapshot in item[1]:
              temp_s1+=snapshot+" "
            run_command(APTLY_EXEC+" publish snapshot -component="+temp_s2+" -distribution="+ARGS['DIST']+" "+temp_s1+" "+ARGS['PUBLISH']+'/'+timestamp)

def aptly_housekeep(keep):
    published_snapshots=run_command(APTLY_EXEC+ " publish list -raw")
    print published_snapshots
    indices=[index for index in range(0,len(published_snapshots),2) if published_snapshots[index+1] == ARGS['DIST']]
    sorted_timestamps=sorted([published_snapshots[index] for index in indices])[:len(indices)-keep]
    #sorted_timestamps=sorted([published_snapshots[index] for index in range(0,len(published_snapshots),2) if published_snapshots[index+1] == ARGS['DIST']])
    print sorted_timestamps
    for timestamp in sorted_timestamps:
        print timestamp
        find_index = published_snapshots.index(timestamp)
        print find_index
    #    run_command(APTLY_EXEC+ " publish drop "+published_snapshots[find_index+1]+" "+published_snapshots[find_index])
          
def display_usage():
    print """   aptly.py -d[--distribution] <distribution> -u[--url] <url> -p[--publish] <publish_path>"

                arguments:
                      -h[--help]         : prints this message
                      -d[distribution]   : distribution eg. vivid or vivid-updates
                      -u[url]            : src url eg. http://ie.archive.ubuntu.com/ubuntu
                      -p[publish]        : path to publish the repo
                      -a[--architectures]: comma separated list of architectures to download packages for. eg. -a amd64,i386
                      -c[--components]   : comma separated list of components to download. eg. -c main,universe

          """                     


def main(argv):

    global ARGS
    global MIRRORS
    global PUBLISHED

    MIRRORS=run_command(APTLY_EXEC+" mirror list -raw")
    PUBLISHED=run_command(APTLY_EXEC+" publish list -raw")

    try:
        opts, args = getopt.getopt(argv,"ha:c:d:u:p:s",["help","filters=","architectures=","components=","distributions=","url=", "publish=","suffix="])
    except getopt.GetoptError:
        display_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            display_usage()
            sys.exit()
        elif opt in ("-d", "--distribution"):
            ARGS.update({"DIST":arg})
        elif opt in ("-u", "--url"):
            ARGS.update({"URL":arg})
        elif opt in ("-p", "--publish"):
            ARGS.update({"PUBLISH":arg})
        elif opt in ("-a", "--architectures"):
            ARGS.update({"ARCHS":arg})
        elif opt in ("-c", "--components"):
            ARGS.update({"COMPONENTS":arg.split(',')})

    if 'ARCHS' not in ARGS:
        ARGS.update({"ARCHS":"amd64"})

    try:
        global TIMESTAMP
        TIMESTAMP='2016-11-03-18-00-00'
        print ARGS
      #  aptly_create_mirrors()
      #  aptly_update_mirrors()
      #  aptly_create_snapshots()
      #  aptly_publish(TIMESTAMP)
        aptly_housekeep(0)
    except BaseException:
        raise


if __name__ == "__main__":
    main(sys.argv[1:])
