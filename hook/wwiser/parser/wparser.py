# -*- coding: utf-8 -*-
# @Author  : Virace
# @Email   : Virace@aliyun.com
# @Site    : x-item.com
# @Software: Pycharm
# @Create  : 2023/10/14 22:53
# @Update  : 2023/10/14 23:02
# @Detail  : 

from wwiser.wwiser.parser.wparser import *
from . import wio

class Parser(object):
    def __init__(self):
        #self._ignore_version = ignore_version
        self._banks = {}
        self._names = None


    def _check_header(self, r, bank):
        root = bank.get_root()
        current = r.current()

        fourcc = r.fourcc()
        if fourcc == b'AKBK':
            # very early versions have a mini header before BKHD
            _unknown = r.u32() #null
            _unknown = r.u32() #null
            r.guess_endian32(0x10)
            fourcc = r.fourcc()

        if fourcc != b'BKHD':
            raise wmodel.VersionError("not a Wwise bank", -1)

        _size = r.u32()


        version = r.u32()
        if version == 0 or version == 1:
            _unknown = r.u32()
            version = r.u32() #actual version in very early banks

        # strange variations
        if version in wdefs.bank_custom_versions:
            version = wdefs.bank_custom_versions[version]
            root.set_custom(True)

        # 'custom' versions start with bitflag 0x80*
        if version & 0xFFFF0000 == 0x80000000:
            logging.warning("parser: unknown custom version %x, may output errors (report)", version)
            version = version & 0x0000FFFF
            root.set_custom(True)

        # in rare cases header is slightly encrypted with 32b values x4, in the game's init code [LIMBO demo, World of Tanks]
        # simulate with a xorpad file (must start with 32b 0, 32b0 then 32b x4 with xors in bank's endianness)
        if version & 0x0FFFF000:
            path = r.get_path()
            if path:
                path += '/'
            path += 'xorpad.bin'
            try:
                with open(path, 'rb') as f:
                    xorpad = f.read()
            except:
                # too limited to recover
                raise wmodel.VersionError("encrypted bank version (needs xorpad.bin)", -1)
            r.set_xorpad(xorpad)
            r.skip(-4)
            version = r.u32() #re-read unxor'd

        # overwrite for cursom versions
        root.set_version(version)
        if version not in wdefs.bank_versions: #not self._ignore_version and
            # allow since there shouldn't be that many changes from known versions
            if version <= wdefs.ancient_versions:
                logging.warning("parser: support for version %i is incomplete and may output errors (can't fix)", version)
            else:
                logging.warning("parser: unknown bank version %i, may output errors (report)", version)
            #raise wmodel.VersionError("unsupported bank version %i" % (version), -1)

        r.seek(current)

        wdefs.setup(version)
        wcls.setup()
        return version

    def parse_banks(self, filenames):
        loaded_filenames = []
        for filename in filenames:
            loaded_filename = self.parse_bank(filename)
            if loaded_filename:
                loaded_filenames.append(loaded_filename)

        logging.info("parser: done")
        return loaded_filenames

    # Parses a whole bank into memory and adds to the list. Can be kinda big (ex. ~50MB in RAM)
    # but since games also load banks in memory should be within reasonable limits.
    def parse_bank(self, filename, raw=None):
        # raw

        if filename in self._banks:
            logging.info("parser: ignoring %s (already parsed)", filename)
            return

        logging.info("parser: parsing %s", filename)

        try:
            if raw is None:
                with open(filename, 'rb') as infile:
                    # real_filename = infile.name
                    r = wio.FileReader(infile)
                    r.guess_endian32(0x04)
                    res = self._process(r, filename)
            else:
                r = wio.FileReader(raw, filename)

                r.guess_endian32(0x04)
                res = self._process(r, filename)

            if res:
                logging.info("parser: %s", res)
                return None

            logging.debug("parser: done %s", filename)
            return filename

        except wio.ReaderError as e:
            error_info = self._print_errors(e)
            logging.error("parser: error parsing %s (corrupted file?), error:\n%s" % (filename, error_info))
            #logging.exception also prints stack trace
        except Exception as e:
            logging.error("parser: error parsing " + filename, e)

        return None

    def _print_errors(self, e):
        import traceback

        # crummy format exception, as python doesn't seem to offer anything decent
        info = []
        trace = traceback.format_exc()
        trace_lines = trace.split('\n')
        trace_lines.reverse()
        for line in trace_lines:
            target_msg = 'Error: '
            if target_msg in line:
                index = line.index(target_msg) + len(target_msg)
                exc_info = '%s- %s' % ('  ' * len(info), line[index:])
                info.append(exc_info)

        #[exceptions.append(line) for line in msg_list if line.startswith('Exception:')]
        text = '\n'.join(info)
        return text

    def _process(self, r, filename):
        bank = wmodel.NodeRoot(r)

        try:
            version = self._check_header(r, bank)

            # first chunk in ancient versions doesn't follow the usual rules
            if version <= 14:
                obj = bank.node('chunk')
                parse_chunk_akbk(obj)

            while not r.is_eof():
                obj = bank.node('chunk')
                parse_chunk(obj)

        except wmodel.VersionError as e:
            return e.msg
        #other exceptions should be handled externally
        #except wmodel.ParseError as e:
            #bank.add_error(str(e))

        if bank.get_error_count() > 0:
            logging.info("parser: ERRORS! %i found (report issue)" % bank.get_error_count())
        if bank.get_skip_count() > 0:
            logging.info("parser: SKIPS! %i found (report issue)" % bank.get_skip_count())

        if self._names:
            bank.set_names(self._names)

        self._banks[filename] = bank
        return None


    def get_banks(self):
        banks = list(self._banks.values())
        return banks

    def get_filenames(self):
        return list(self._banks.keys())

    def set_names(self, names):
        self._names = names
        for bank in self._banks.values():
            bank.set_names(names)

    #def set_ignore_version(self, value):
    #    self._ignore_version = value

    def unload_bank(self, filename):
        if filename not in self._banks:
            logging.warn("parser: can't unload " + filename)
            return

        logging.info("parser: unloading " + filename)
        self._banks.pop(filename)
