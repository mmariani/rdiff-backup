import unittest, os
from commontest import *
from rdiff_backup import Globals, SetConnections, log, rpath


"""Regression tests

This one must be run in the rdiff-backup directory, as it requres
chdir-wrapper, the various rdiff-backup files, and the directory
testfiles
"""

Globals.set('change_source_perms', 1)
Globals.counter = 0
log.Log.setverbosity(7)

class Local:
	"""This is just a place to put increments relative to the local
	connection"""
	def get_local_rp(extension):
		return rpath.RPath(Globals.local_connection, "testfiles/" + extension)

	inc1rp = get_local_rp('increment1')
	inc2rp = get_local_rp('increment2')
	inc3rp = get_local_rp('increment3')
	inc4rp = get_local_rp('increment4')

	rpout = get_local_rp('output')
	rpout_inc = get_local_rp('output_inc')
	rpout1 = get_local_rp('restoretarget1')
	rpout2 = get_local_rp('restoretarget2')
	rpout3 = get_local_rp('restoretarget3')
	rpout4 = get_local_rp('restoretarget4')

	noperms = get_local_rp('noperms')
	noperms_out = get_local_rp('noperms_output')

	rootfiles = get_local_rp('root')
	rootfiles2 = get_local_rp('root2')
	rootfiles21 = get_local_rp('root2.1')
	rootfiles_out = get_local_rp('root_output')
	rootfiles_out2 = get_local_rp('root_output2')

	prefix = get_local_rp('.')


class PathSetter(unittest.TestCase):
	def get_prefix_and_conn(self, path, return_path):
		"""Return (prefix, connection) tuple"""
		if path:
			return (return_path,
					SetConnections.init_connection("./chdir-wrapper "+path))
		else: return ('./', Globals.local_connection)

	def get_src_rp(self, path):
		return rpath.RPath(self.src_conn, self.src_prefix + path)

	def get_dest_rp(self, path):
		return rpath.RPath(self.dest_conn, self.dest_prefix + path)

	def set_rbdir(self, rpout):
		"""Create rdiff-backup-data dir if not already, tell everyone"""
		self.rbdir = self.rpout.append('rdiff-backup-data')
		self.rpout.mkdir()
		self.rbdir.mkdir()
		SetConnections.UpdateGlobal('rbdir', self.rbdir)

	def setPathnames(self, src_path, src_return, dest_path, dest_return):
		"""Start servers which will run in src_path and dest_path respectively

		If either is None, then no server will be run and local
		process will handle that end.  src_return and dest_return are
		the prefix back to the original rdiff-backup directory.  So
		for instance is src_path is "test2/tmp", then src_return will
		be '../'.

		"""
		# Clear old data that may rely on deleted connections
		Globals.isbackup_writer = None
		Globals.isbackup_reader = None
		Globals.rbdir = None

		print "Setting up connection"
		self.src_prefix, self.src_conn = \
						 self.get_prefix_and_conn(src_path, src_return)
		self.dest_prefix, self.dest_conn = \
						  self.get_prefix_and_conn(dest_path, dest_return)
		SetConnections.BackupInitConnections(self.src_conn, self.dest_conn)

		assert not os.system("rm -rf testfiles/output* "
							 "testfiles/restoretarget* "
							 "testfiles/noperms_output testfiles/root_output "
							 "testfiles/unreadable_out")

		self.inc1rp = self.get_src_rp("testfiles/increment1")
		self.inc2rp = self.get_src_rp('testfiles/increment2')
		self.inc3rp = self.get_src_rp('testfiles/increment3')
		self.inc4rp = self.get_src_rp('testfiles/increment4')

		self.rpout_inc = self.get_dest_rp('testfiles/output_inc')
		self.rpout1 = self.get_dest_rp('testfiles/restoretarget1')
		self.rpout2 = self.get_dest_rp('testfiles/restoretarget2')
		self.rpout3 = self.get_dest_rp('testfiles/restoretarget3')
		self.rpout4 = self.get_dest_rp('testfiles/restoretarget4')

		self.rpout = self.get_dest_rp('testfiles/output')
		self.set_rbdir(self.rpout)

		self.noperms = self.get_src_rp('testfiles/noperms')
		self.noperms_out = self.get_dest_rp('testfiles/noperms_output')

		self.rootfiles = self.get_src_rp('testfiles/root')
		self.rootfiles_out = self.get_dest_rp('testfiles/root_output')
		self.rootfiles2 = self.get_src_rp('testfiles/root2')
		self.rootfiles21 = self.get_src_rp('testfiles/root2.1')
		self.rootfiles_out2 = self.get_dest_rp('testfiles/root_output2')
		
		self.one_unreadable = self.get_src_rp('testfiles/one_unreadable')
		self.one_unreadable_out = self.get_dest_rp('testfiles/unreadable_out')

	def tearDown(self):
		print "Taking down connections"
		SetConnections.CloseConnections()


class IncrementTest1(unittest.TestCase):
	dirlist = ["testfiles/increment1", "testfiles/increment2",
			   "testfiles/increment3", "testfiles/increment4"]
	gzip_dirlist = ["testfiles/gzips/inc1", "testfiles/gzips/inc2"]

	def testLocalGzipinc(self):
		"""Local test small archive which exercises gzip options"""
		BackupRestoreSeries(1, 1, self.gzip_dirlist)

	def testRemoteBothGzipinc(self):
		"""Remote test small archive which exercises gzip options"""
		BackupRestoreSeries(None, None, self.gzip_dirlist)

	def testLocalinc(self):
		"""Test self.incrementing, and then restoring, local"""
		BackupRestoreSeries(1, 1, self.dirlist)
		
	def test_remote_src(self):
		"""Increment/Restore when source directory is remote"""
		BackupRestoreSeries(None, 1, self.dirlist)
		
	def test_remote_dest(self):
		"""Increment/Restore when target directory is remote"""
		BackupRestoreSeries(1, None, self.dirlist)		
		
	def test_remote_both(self):
		"""Increment/Restore when both directories are remote"""
		BackupRestoreSeries(None, None, self.dirlist)


class IncrementTest2(PathSetter):
	def OldtestRecoveryLocal(self):
		"""Test to see if rdiff-backup can continue with bad increment"""
		assert not os.system("rm -rf testfiles/recovery_out_backup")
		self.setPathnames(None, None, None, None)
		Time.setprevtime(1006136450)
		Time.setcurtime()
		Globals.add_regexp('.*rdiff-backup-data', 1)
		os.system('cp -a testfiles/recovery_out testfiles/recovery_out_backup')
		recovery_in = self.get_src_rp('testfiles/recovery')
		recovery_out = self.get_dest_rp('testfiles/recovery_out_backup')
		recovery_inc = self.get_dest_rp('testfiles/recovery_out_backup/'
										'rdiff-backup-data/increments')
		highlevel.Mirror_and_increment(recovery_in, recovery_out, recovery_inc)
		# Should probably check integrity of increments, but for now
		# allow if it doesn't during the Mirror_and_increment

	def OldtestRecoveryRemote(self):
		"""Test Recovery with both connections remote"""
		assert not os.system('rm -rf testfiles/recovery_out_backup')
		self.setPathnames('test1', '../', 'test2/tmp', '../../')
		Time.setprevtime(1006136450)
		Time.setcurtime()
		Globals.add_regexp('.*rdiff-backup-data', 1)
		os.system('cp -a testfiles/recovery_out testfiles/recovery_out_backup')
		recovery_in = self.get_src_rp('testfiles/recovery')
		recovery_out = self.get_dest_rp('testfiles/recovery_out_backup')
		recovery_inc = self.get_dest_rp('testfiles/recovery_out_backup/'
										'rdiff-backup-data/increments')
		highlevel.Mirror_and_increment(recovery_in, recovery_out, recovery_inc)
		# Should probably check integrity of increments, but for now
		# allow if it doesn't during the Mirror_and_increment

	def runtest(self):
		"""After setting connections, etc., run actual test using this"""
		Time.setcurtime()

		Main.backup_set_select(Local.inc1rp)
		highlevel.Mirror(self.inc1rp, self.rpout)
		assert CompareRecursive(Local.inc1rp, Local.rpout)

		Time.setcurtime()
		Time.setprevtime(999500000)
		Main.backup_set_select(self.inc2rp)
		highlevel.Mirror_and_increment(self.inc2rp, self.rpout, self.rpout_inc)
		assert CompareRecursive(Local.inc2rp, Local.rpout)

		Time.setcurtime()
		Time.setprevtime(999510000)
		Main.backup_set_select(self.inc3rp)
		highlevel.Mirror_and_increment(self.inc3rp, self.rpout, self.rpout_inc)
		assert CompareRecursive(Local.inc3rp, Local.rpout)

		Time.setcurtime()
		Time.setprevtime(999520000)
		Main.backup_set_select(self.inc4rp)
		highlevel.Mirror_and_increment(self.inc4rp, self.rpout, self.rpout_inc)
		assert CompareRecursive(Local.inc4rp, Local.rpout)
		

		print "Restoring to self.inc4"
		highlevel.Restore(999530000, self.rpout, self.get_inctup(),
						  self.rpout4)
		assert CompareRecursive(Local.inc4rp, Local.rpout4)

		print "Restoring to self.inc3"
		highlevel.Restore(999520000, self.rpout, self.get_inctup(),
						  self.rpout3)
		assert CompareRecursive(Local.inc3rp, Local.rpout3)

		print "Restoring to self.inc2"
		highlevel.Restore(999510000, self.rpout, self.get_inctup(),
						  self.rpout2)
		assert CompareRecursive(Local.inc2rp, Local.rpout2)

		print "Restoring to self.inc1"
		highlevel.Restore(999500000, self.rpout, self.get_inctup(),
						  self.rpout1)
		assert CompareRecursive(Local.inc1rp, Local.rpout1)

	def get_inctup(self):
		"""Return inc tuples as expected by Restore.RestoreRecursive

		Assumes output increment directory is
		testfiles/output_inc._____.

		"""
		filenames = filter(lambda x: x.startswith("output_inc."),
						   Local.prefix.listdir())
		rplist = map(lambda x: Local.prefix.append(x), filenames)
		return IndexedTuple((), (Local.prefix.append("output_inc"), rplist))


class MirrorTest(PathSetter):
	"""Test some mirroring functions"""
	def testLocalMirror(self):
		"""Test Local mirroring"""
		self.setPathnames(None, None, None, None)
		self.runtest()

	def testPartialLocalMirror(self):
		"""Test updating an existing directory"""
		self.setPathnames(None, None, None, None)
		self.run_partial_test()

	def testRemoteMirror(self):
		"""Mirroring when destination is remote"""
		self.setPathnames(None, None, 'test1', '../')
		self.runtest()

	def testPartialRemoteMirror(self):
		"""Partial mirroring when destination is remote"""
		self.setPathnames(None, None, 'test1', '../')
		self.run_partial_test()

	def testSourceRemoteMirror(self):
		"""Mirroring when source is remote"""
		self.setPathnames('test2', '../', None, None)
		self.runtest()

	def testPartialSourceRemoteMirror(self):
		"""Partial Mirroring when source is remote"""
		self.setPathnames('test2', '../', None, None)
		self.run_partial_test()

	def testBothRemoteMirror(self):
		"""Mirroring when both directories are remote"""
		self.setPathnames('test1', '../', 'test2/tmp', '../../')
		self.runtest()

	def testPartialBothRemoteMirror(self):
		"""Partial mirroring when both directories are remote"""
		self.setPathnames('test1', '../', 'test2/tmp', '../../')
		self.run_partial_test()

	def testPermSkipLocal(self):
		"""Test to see if rdiff-backup will skip unreadable files"""
		self.setPathnames(None, None, None, None)
		Globals.change_source_perms = None
		Time.setcurtime()
		self.Mirror(self.one_unreadable, self.one_unreadable_out)
		Globals.change_source_perms = 1
		self.Mirror(self.one_unreadable, self.one_unreadable_out)
		# Could add test, but for now just make sure it doesn't exit

	def testPermSkipRemote(self):
		"""Test skip of unreadable files remote"""
		self.setPathnames('test1', '../', 'test2/tmp', '../../')
		Globals.change_source_perms = None
		Time.setcurtime()
		self.Mirror(self.one_unreadable, self.one_unreadable_out)
		Globals.change_source_perms = 1
		self.Mirror(self.one_unreadable, self.one_unreadable_out)
		# Could add test, but for now just make sure it doesn't exit

	def refresh(self, *rps):
		for rp in rps: rp.setdata()

	def _testRootLocal(self):
		"""Test mirroring a directory with dev files and different owners"""
		self.setPathnames(None, None, None, None)
		Globals.change_ownership = 1
		self.refresh(self.rootfiles, self.rootfiles_out,
				Local.rootfiles, Local.rootfiles_out) # add uid/gid info
		highlevel.Mirror(self.rootfiles, self.rootfiles_out)
		assert CompareRecursive(Local.rootfiles, Local.rootfiles_out)
		Globals.change_ownership = None
		self.refresh(self.rootfiles, self.rootfiles_out,
				Local.rootfiles, Local.rootfiles_out) # remove that info

	def _testRootRemote(self):
		"""Mirroring root files both ends remote"""
		self.setPathnames('test1', '../', 'test2/tmp', '../../')
		for conn in Globals.connections:
			conn.Globals.set('change_ownership', 1)
		self.refresh(self.rootfiles, self.rootfiles_out,
				Local.rootfiles, Local.rootfiles_out) # add uid/gid info
		highlevel.Mirror(self.rootfiles, self.rootfiles_out)
		assert CompareRecursive(Local.rootfiles, Local.rootfiles_out)
		for coon in Globals.connections:
			conn.Globals.set('change_ownership', None)
		self.refresh(self.rootfiles, self.rootfiles_out,
				Local.rootfiles, Local.rootfiles_out) # remove that info

	def testRoot2Local(self):
		"""Make sure we can backup a directory we don't own"""
		self.setPathnames(None, None, None, None)
		Globals.change_ownership = Globals.change_source_perms = None
		self.refresh(self.rootfiles2, self.rootfiles_out2,
				Local.rootfiles2, Local.rootfiles_out2) # add uid/gid info
		self.Mirror(self.rootfiles2, self.rootfiles_out2)
		assert CompareRecursive(Local.rootfiles2, Local.rootfiles_out2)
		self.refresh(self.rootfiles2, self.rootfiles_out2,
				Local.rootfiles2, Local.rootfiles_out2) # remove that info
		self.Mirror(self.rootfiles21, self.rootfiles_out2)
		assert CompareRecursive(Local.rootfiles21, Local.rootfiles_out2)
		self.refresh(self.rootfiles21, self.rootfiles_out2,
				Local.rootfiles21, Local.rootfiles_out2) # remove that info
		Globals.change_source_perms = 1
		
	def deleteoutput(self):
		assert not os.system("rm -rf testfiles/output*")
		self.rbdir = self.rpout.append('rdiff-backup-data')
		self.rpout.mkdir()
		self.rbdir.mkdir()
		self.reset_rps()

	def reset_rps(self):
		"""Use after external changes made, to update the rps"""
		for rp in [self.rpout, Local.rpout,
				   self.rpout_inc, Local.rpout_inc,
				   self.rpout1, Local.rpout1,
				   self.rpout2, Local.rpout2,
				   self.rpout3, Local.rpout3,
				   self.rpout4, Local.rpout4]:
			rp.setdata()
		
	def runtest(self):
		Time.setcurtime()
		assert self.rbdir.lstat()
		self.Mirror(self.inc1rp, self.rpout)
		assert CompareRecursive(Local.inc1rp, Local.rpout)

		self.deleteoutput()

		self.Mirror(self.inc2rp, self.rpout)
		assert CompareRecursive(Local.inc2rp, Local.rpout)

	def run_partial_test(self):
		assert not os.system("rm -rf testfiles/output")
		assert not os.system("cp -a testfiles/increment3 testfiles/output")
		self.reset_rps()

		Time.setcurtime()
		self.Mirror(self.inc1rp, self.rpout)
		#rpath.RPath.copy_attribs(self.inc1rp, self.rpout)
		assert CompareRecursive(Local.inc1rp, Local.rpout)

		self.Mirror(self.inc2rp, self.rpout)
		assert CompareRecursive(Local.inc2rp, Local.rpout)

	def Mirror(self, rpin, rpout):
		"""Like highlevel.Mirror, but run misc_setup first"""
		Main.force = 1
		Main.misc_setup([rpin, rpout])
		Main.backup_set_select(rpin)
		Main.backup_init_dirs(rpin, rpout)
		highlevel.Mirror(rpin, rpout)
		Log.close_logfile()
		Hardlink.clear_dictionaries()

if __name__ == "__main__": unittest.main()
