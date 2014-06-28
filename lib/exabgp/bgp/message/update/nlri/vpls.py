# encoding: utf-8
"""
vpls.py

Created by Nikita Shirokov on 2014-06-16.
Copyright (c) 2014-2014 Nikita Shirokov. All rights reserved.
Copyright (c) 2014-2014 Exa Networks. All rights reserved.
"""

from struct import unpack, pack
from exabgp.protocol.family import AFI,SAFI
from exabgp.bgp.message.direction import OUT
from exabgp.bgp.message.notification import Notify
from exabgp.bgp.message.update.nlri.nlri import NLRI
from exabgp.bgp.message.update.nlri.qualifier.rd import RouteDistinguisher
from exabgp.bgp.message.update.attribute.nexthop import NextHop

def _unique ():
	value = 0
	while True:
		yield value
		value += 1

unique = _unique()

class VPLSNLRI (NLRI):
	def __init__ (self,rd,ve,base,offset,size):
		NLRI.__init__(self,AFI.l2vpn,SAFI.vpls)
		self.action = OUT.announce
		self.nexthop = None
		self.rd = rd
		self.base = base
		self.offset = offset
		self.size = size
		self.ve = ve
		self.unique = unique.next()

	def index (self):
		return self.pack()

	def pack (self, addpath=None):
		return '%s%s%s%s' % (
			'\x00\x11',  # pack('!H',17)
			self.rd.pack(),
			pack('!HHH',
				self.ve,
				self.offset,
				self.size
			),
			pack('!L',(self.base<<4)|0x1)[1:]  # setting the bottom of stack, should we ?
		)

	# XXX: FIXME: we need an unique key here.
	# XXX: What can we use as unique key ?
	def json (self):
		content = ','.join([
			self.rd.json(),
			'"endpoint": "%s"' % self.ve,
			'"base": "%s"' % self.offset,
			'"offset": "%s"' % self.size,
			'"size": "%s"' % self.base,
		])
		return '"vpls-%s": { %s }' % (self.unique, content)

	def extensive (self):
		return "vpls%s endpoint %s base %s offset %s size %s %s" % (
			self.rd,
			self.ve,
			self.base,
			self.offset,
			self.size,
			'' if self.nexthop is None else 'next-hop %s' % self.nexthop,
		)

	def __str__ (self):
		return self.extensive()

	@staticmethod
	def unpack (cls,afi,safi,nexthop,data,action):
		# label is 20bits, stored using 3 bytes, 24 bits
		length, = unpack('!H',data[0:2])
		if len(data) != length+2:
			raise Notify(3,10,'l2vpn vpls message length is not consistent with encoded data')
		rd = RouteDistinguisher(data[2:10])
		ve,offset,size = unpack('!HHH',data[10:16])
		base = unpack('!L','\x00'+data[16:19])[0]>>4
		nlri = cls(rd,ve,base,offset,size)
		nlri.action = action
		nlri.nexthop = NextHop.unpack(nexthop)
		return len(data), nlri

for safi in (SAFI.vpls,):
	for afi in (AFI.l2vpn,):
		VPLSNLRI.register(afi,safi)
