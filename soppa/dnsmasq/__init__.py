import os

from soppa.contrib import *

"""
Setup *.dev to point to 127.0.0.1
DNS /etc/resolver/dev
domain mapping /usr/local/etc/dnsmasq.conf
usage: aslocal dnsmasq:setup
"""
class Dnsmasq(Soppa):
    tld='dev'
    port='127.0.0.1'
    daemons_dir='/Library/LaunchDaemons/'
    brewtool='homebrew.mxcl.dnsmasq.plist'
    needs=[
        'soppa.file',
        'soppa.operating',
    ]

    def setup():
        if self.operating.is_osx():
            self.run('brew install dnsmasq')
            if not self.exists('/usr/local/etc/dnsmasq.conf'):
                self.run('cp $(brew list dnsmasq | grep /dnsmasq.conf.example$) /usr/local/etc/dnsmasq.conf')
            if not self.exists('/Library/LaunchDaemons/homebrew.mxcl.dnsmasq.plist'):
                self.sudo('cp $(brew list dnsmasq | grep /homebrew.mxcl.dnsmasq.plist$) /Library/LaunchDaemons/')

        self.file.set_setting('/usr/local/etc/dnsmasq.conf', 'address=/.{dnsmasq_tld}/{dnsmasq_port}')
        self.sudo('mkdir -p /etc/resolver && touch /etc/resolver/{dnsmasq_tld}')
        self.file.set_setting('/etc/resolver/{dnsmasq_tld}', 'nameserver {dnsmasq_port}')

    def startcmd():
        self.sudo('launchctl load /Library/LaunchDaemons/homebrew.mxcl.dnsmasq.plist')

    def stopcmd():
        self.sudo('launchctl unload /Library/LaunchDaemons/homebrew.mxcl.dnsmasq.plist')
