"""
To use these samples:
pip install statsd requests
"""
import statsd, random, time, requests
c = statsd.StatsClient('localhost', 8125)

FLUSH_INTERVAL = 10.1

def registrations():
    """
    /render/?width=586&height=308&from=-20minutes&target=stats.gauges.user_registrations
    /render/?width=586&height=308&from=-20minutes&target=derivative(stats.gauges.user_registrations)
    
    """
    user_registrations = 1
    while True:
        user_registrations += random.randint(1, 128)
        c.gauge('user_registrations', user_registrations)
        time.sleep(FLUSH_INTERVAL)

def responsetimes(url):
    while True:
        r = requests.get(url)
        took = int(r.elapsed.microseconds/1000)
        c.timing('mainpage', took)
        time.sleep(FLUSH_INTERVAL)
    
