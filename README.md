svd_util
========

python utility funcs, classes, small languages+frameworks, scripts. 
old or new.. collection.
i tend to use most optz, attr, struct, py3, eutf

[[ me and software|http://www.svilendobrev.com/rabota/ ]]

--------

* [[assignment_order.py|https://github.com/svilendobrev/svd_util/blob/master/assignment_order.py]] : Obtain order of assigments in python source text namespaces.
* [[attr.py|https://github.com/svilendobrev/svd_util/blob/master/attr.py]] : additional python-reflection tools: - multilevel getattr, setattr, import, getitemer - local vs see-through-hierarchy getattr - fail-proof issubclass() - subclasses extractor
* [[bin/doprof.py|https://github.com/svilendobrev/svd_util/blob/master/bin/doprof.py]] : better view onto python profiler results
* [[bin/filter-output.py|https://github.com/svilendobrev/svd_util/blob/master/bin/filter-output.py]] : filter (=count-generalize) instance-or-run -specific things, e.g. memory addresses, to compare different test runs
* [[bin/moddump.py|https://github.com/svilendobrev/svd_util/blob/master/bin/moddump.py]] : try describe all about a python module - name,path,doc,items
* [[bin/oneliner.py|https://github.com/svilendobrev/svd_util/blob/master/bin/oneliner.py]] : generate a (wiki) page from first __doc__ line/para of input python files (e.g. for github)
* [[bin/py2utf.py|https://github.com/svilendobrev/svd_util/blob/master/bin/py2utf.py]] : autoconvert (source-files) from cp1251 to utf AND fix the "coding" line
* [[bin/sortsqlitedump.py|https://github.com/svilendobrev/svd_util/blob/master/bin/sortsqlitedump.py]] : sort/reorder sqlite .dump, for comparable outputs
* [[bokluk.py|https://github.com/svilendobrev/svd_util/blob/master/bokluk.py]] : useful setup for gc-debugging
* [[class_attr.py|https://github.com/svilendobrev/svd_util/blob/master/class_attr.py]] : various descriptors for class-level-attributes
* [[config.py|https://github.com/svilendobrev/svd_util/blob/master/config.py]] : hierarchical namespaced configuration language/engine, with types, helps, inheritance
* [[cron.py|https://github.com/svilendobrev/svd_util/blob/master/cron.py]] : parse+create of cron/crontab files
* [[datetimez.py|https://github.com/svilendobrev/svd_util/blob/master/datetimez.py]] : symmetric datetime conversions to/from text.
* [[dbg.py|https://github.com/svilendobrev/svd_util/blob/master/dbg.py]] : various debug utilities: stack-level-counter, call-stack inspections
* [[dictOrder.py|https://github.com/svilendobrev/svd_util/blob/master/dictOrder.py]] : ordered dictionary (by-item-creation)
* [[dicts.py|https://github.com/svilendobrev/svd_util/blob/master/dicts.py]] : key-translating dictionaries - lowercase, map; dictOrder_fromstr
* [[diff.py|https://github.com/svilendobrev/svd_util/blob/master/diff.py]] : wrapper and ignore_space for difflib
* [[escaping_codec.py|https://github.com/svilendobrev/svd_util/blob/master/escaping_codec.py]] : escape/unescape strings
* [[eutf.py|https://github.com/svilendobrev/svd_util/blob/master/eutf.py]] : guess utf or byte-encoding, and (on-the-fly) conversion, on text or files. python2 + python3
* [[expr.py|https://github.com/svilendobrev/svd_util/blob/master/expr.py]] : expression-tree builder and visitor/evaluator (language)
* [[facer.py|https://github.com/svilendobrev/svd_util/blob/master/facer.py]] : interface/protocol/API declaration language. Methods, arguments, results - types, cardinality, optionality; inheritance, specialization, cloning. Use visitors to do/generate all else.
* [[fileCache.py|https://github.com/svilendobrev/svd_util/blob/master/fileCache.py]] : cache content of a file + property doing it
* [[forward_resolver.py|https://github.com/svilendobrev/svd_util/blob/master/forward_resolver.py]] : forward-declared module.attr resolver.
* [[func2code.py|https://github.com/svilendobrev/svd_util/blob/master/func2code.py]] : inspect variables used in function, local/global - for tracing/explain
* [[gencxx.py|https://github.com/svilendobrev/svd_util/blob/master/gencxx.py]] : around generating code - C, python, vim
* [[hacksrc.py|https://github.com/svilendobrev/svd_util/blob/master/hacksrc.py]] : source-monkey-patcher for python - extract+patch+compile a func
* [[html_visitor.py|https://github.com/svilendobrev/svd_util/blob/master/html_visitor.py]] : html structural visitor/extractor
* [[htmlcodec.py|https://github.com/svilendobrev/svd_util/blob/master/htmlcodec.py]] : various html escapers
* [[jgenerator.py|https://github.com/svilendobrev/svd_util/blob/master/jgenerator.py]] : model-description "language" + dialects + generator of equivalent model in java + SAX + sqlite
* [[lat2cyr.py|https://github.com/svilendobrev/svd_util/blob/master/lat2cyr.py]] : cyrillic transcripting to/from latin - e.g. qwerty, SMS, sounds-like, looks-like, etc
* [[minsec.py|https://github.com/svilendobrev/svd_util/blob/master/minsec.py]] : time minutes-seconds-frames conversions/prettyprint
* [[mix.py|https://github.com/svilendobrev/svd_util/blob/master/mix.py]] : mix: logging destructor, valid weakref wrapper, Functor, mutex, neighbours-in-sequence ..
* [[module.py|https://github.com/svilendobrev/svd_util/blob/master/module.py]] : python module tools
* [[money_formatter.py|https://github.com/svilendobrev/svd_util/blob/master/money_formatter.py]] : text-format amount of money
* [[optz.py|https://github.com/svilendobrev/svd_util/blob/master/optz.py]] : simple !! options-getter (wrapping optparse or else)
* [[osextra.py|https://github.com/svilendobrev/svd_util/blob/master/osextra.py]] : extra os-level funcs - execresult, touch, ..
* [[py/parser3.py|https://github.com/svilendobrev/svd_util/blob/master/py/parser3.py]] : fixed variant of py3:html.parser: m = attrfind_tolerant.search(rawdata[:endpos], k)
* [[py/unquote3.py|https://github.com/svilendobrev/svd_util/blob/master/py/unquote3.py]] : py2 version of py3 urllib.parse.unquote
* [[py3.py|https://github.com/svilendobrev/svd_util/blob/master/py3.py]] : using same code for python2 and python3
* [[recorder.py|https://github.com/svilendobrev/svd_util/blob/master/recorder.py]] : recorder + re-player of object usage - method calls with their args
* [[rim_digit.py|https://github.com/svilendobrev/svd_util/blob/master/rim_digit.py]] : rome digits to numeric
* [[setOrder.py|https://github.com/svilendobrev/svd_util/blob/master/setOrder.py]] : ordered set - by-item-creation
* [[slovom.py|https://github.com/svilendobrev/svd_util/blob/master/slovom.py]] : numbers in words in Bulgarian  2008? friends | числа словом
* [[stacks.py|https://github.com/svilendobrev/svd_util/blob/master/stacks.py]] : stack with automatic (ref-counted) cleanup/pop
* [[str.py|https://github.com/svilendobrev/svd_util/blob/master/str.py]] : hierarchical str()/print; notSetYet singleton
* [[struct.py|https://github.com/svilendobrev/svd_util/blob/master/struct.py]] : structure as dict as structure, attr-to-item, set-keyword-attrs with allowed/mandatory-validation
* [[testeng/|https://github.com/svilendobrev/svd_util/blob/master/testeng/]] : testing engine with analysis/data-oriented syntax/structure of cases; simple single-or-multi-case unittestcase
* [[timezone.py|https://github.com/svilendobrev/svd_util/blob/master/timezone.py]] : some usable default timezone implementation
* [[tracer.py|https://github.com/svilendobrev/svd_util/blob/master/tracer.py]] : trace+explain/log runtime python code - instrumentation of variables, methods
* [[txt.py|https://github.com/svilendobrev/svd_util/blob/master/txt.py]] : text encodings, escaping, whitespace stripping
* [[ui/|https://github.com/svilendobrev/svd_util/blob/master/ui/]] : language/engine for dialog/form layout description - text-parser, tree-builder, fields; menus
* [[url.py|https://github.com/svilendobrev/svd_util/blob/master/url.py]] : symmetrical url-to/from-dict conversions
* [[url_cyr2regexp.py|https://github.com/svilendobrev/svd_util/blob/master/url_cyr2regexp.py]] : cyrillic urls into apache regexps/rewrites - multi-transcriptions, 1251/utf, ignorecase, etc
* [[validator4regexp.py|https://github.com/svilendobrev/svd_util/blob/master/validator4regexp.py]] : validators using regexps
* [[vreme.py|https://github.com/svilendobrev/svd_util/blob/master/vreme.py]] : Universal Calendar Time and Pediods and arithmetics; physical, logical (next-working-day), inherit/compose, count, compare, overlap, cut
* [[wither.py|https://github.com/svilendobrev/svd_util/blob/master/wither.py]] : empty context for with operator - i.e. with (somefile or wither): ...
* [[xcalc2.py|https://github.com/svilendobrev/svd_util/blob/master/xcalc2.py]] : wave-like dependency-tree expression/rule re-calculation
* [[xml2obj.py|https://github.com/svilendobrev/svd_util/blob/master/xml2obj.py]] : xml into object, multi-language values
* [[yamls/|https://github.com/svilendobrev/svd_util/blob/master/yamls/]] : usability-tuned yaml i/o - human re-editable - aligned, ordered, min-clutter
