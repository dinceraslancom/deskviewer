def main():
    print('''
    Basic Usage:
    
    $ deskviewer.publish
    Server Starting 0.0.0.0:8765
    
    $ deskviewer.connect -H 192.168.x.x
    Connecting Server 192.168.x.x:8765    

    Advanced Usage:
    
    $ deskviewer.publish -u user -p pass -b 0.0.0.0 --port 8765
    Server Starting 0.0.0.0:8765

    $ deskviewer.connect -u user -p pass -H 192.168.x.x --port 8765 --quality high
    Connecting Server 192.168.x.x:8765    
    ''')