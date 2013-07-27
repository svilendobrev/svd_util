SVD_UTIL	?=../../..
#DIVAN    	?=../..
DIVANTEST	?=.
PYTHONPATH = .:..:$(SVD_UTIL)
#$(DIVAN):
export PYTHONPATH

MAKEFLAGS=j1

%.t: %.py db
	python $< --url http://tt:tt@localhost:55984
#	--nousers

#z: map_d2u.t

DIVANTESTS += users sec4db desdefs
DIVANTESTS += cc itemset

testdivan: $(DIVANTESTS:%=%.t)

#obs: regdis.t obser.t signaler.t
#id: idaddr.t
#t: tag.t


db:
	echo '[admins]' > _couchdb.ini
	echo 'tt = tt' >> _couchdb.ini
	$(MAKE) _mycouchdb _mycouchdb_ARGS="-a _couchdb.ini"
dbrestart: dbstop
	rm -rf ./_couchdb
	$(MAKE) db
dbstop:
	$(MAKE) _mycouchdb _mycouchdb_ARGS=-d

_mycouchdb:
	mkdir -p _couchdb
	couchdb -a $(DIVANTEST)/couchdb.ini -p _couchdb/couchdb.pid -o _couchdb/couchdb.stdout -e _couchdb/couchdb.stderr -b $(_mycouchdb_ARGS)
# vim:ts=4:sw=4:noexpandtab
