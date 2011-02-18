#!/bin/bash

#cd swig


#swig -python -c++ -lstl.i -lstd_vector.i -lstd_string.i reverse_dic.i
#g++ -fpic -I/usr/include/python2.5 -I/usr/lib/python2.5/config -c reverse_dic.h reverse_dic.cpp reverse_dic_wrap.cxx
#gcc -shared -o _reverse_dic.so reverse_dic.o reverse_dic_wrap.o /usr/lib/libstdc++.so.6.0.*

#from _reverse_dic import *
#text=file("/media/MyFlash8/dic-work/tmp-dic/quick_eng-persian.txt").read()
#search(text, "سلام", 0.1, 100, "،", True, "Percent")

if [ "$1" = babylon ] ; then
  echo "Running SWIG ..." &&\
  swig -classic -python -c++ -lstl.i babylon.i &&\
  echo "Running G++ ..." &&\
  g++ -fpic -I/usr/include/python2.5 -I/usr/lib/python2.5/config -c babylon.h babylon.cpp babylon_wrap.cxx &&\
  echo "Running GCC ..." &&\
  gcc -shared -o _babylon.so babylon.o babylon_wrap.o /usr/lib/libstdc++.so.6.0.* -lz &&\
  mv _babylon.so ../../lib
fi
## _babylon module for windows (failed...)
#swig -python -c++ -lstl.i babylon.i -fpic 
#wine z:/home/tux/CodeBlocks/MinGW/bin/g++.exe -fpic -Iz:/home/tux/CodeBlocks/MinGW/include/python2.5/ -c babylon.h
## babylon.h:1: warning: -fpic ignored for target (all code is position independent
## babylon.h:206: error: `gzFile' does not name a type"




if [ "$1" = mdicbuilder ] ; then
  swig -python -c++ -lstl.i mdicbuilder.i
  g++ -fpic -I/usr/include/python2.5 -I/usr/lib/python2.5/config -c mdicbuilder.h mdicbuilder.cpp mdicbuilder_wrap.cxx
  gcc -shared -o _mdicbuilder.so mdicbuilder.o mdicbuilder_wrap.o /usr/lib/libstdc++.so.6.0.* -lsqlite3

  mv _mdicbuilder.so ..
fi



if [ "$1" = stardictbuilder ] ; then
  swig -python -c++ -lstl.i -lstd_vector.i -lstd_string.i stardictbuilder.i
  g++ -fpic -I/usr/include/python2.5 -I/usr/lib/python2.5/config -c stardictbuilder.h stardictbuilder.cpp stardictbuilder_wrap.cxx
  gcc -shared -o _stardictbuilder.so stardictbuilder.o stardictbuilder_wrap.o /usr/lib/libstdc++.so.6.0.*

  mv _stardictbuilder.so ..
fi

if [ "$1" = stardict ] ; then
  swig -python -c++ -lstl.i -lstd_vector.i -lstd_string.i stardict.i
  g++ -fpic -I/usr/include/python2.5 -I/usr/lib/python2.5/config -c stardict.h stardict.cpp stardict_wrap.cxx
  gcc -shared -o _stardict.so stardict.o stardict_wrap.o /usr/lib/libstdc++.so.6.0.* -lz

  mv _stardict.so ..
fi

#swig -python -c++ -lstl.i -lstd_vector.i -lstd_string.i vector.i
#g++ -fpic -I/usr/include/python2.5 -I/usr/lib/python2.5/config -c vector_wrap.cxx
#gcc -shared -o _vector.so vector_wrap.o /usr/lib/libstdc++.so.6.0.*
#mv _vector.so ..

if [ "$1" = clean ] ; then
  rm *.o *.cxx *.gch *.so
fi


