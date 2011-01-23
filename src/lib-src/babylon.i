//babylon.i
%module babylon
%include stl.i
%{
#include "babylon.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iconv.h>
#include <zlib.h>
//#include <gzip.hpp>
%}

const std::string bgl_language[];
const std::string bgl_charsetname[];
const std::string bgl_charset[];
const std::string partOfSpeech[];

typedef struct bgl_block;
typedef struct bgl_entry;




class Babylon{
public:
  Babylon( std::string filename );
  ~Babylon();
  bool open();
  void close();
  bool readBlock( bgl_block &block );
  bool read();
  bgl_entry readEntry();

    // from babylon.h
    inline std::string title() const ;
    inline std::string author() const ;
    inline std::string email() const ;
    inline std::string description() const ;
    inline std::string copyright() const ;
    inline std::string sourceLang() const ;
    inline std::string targetLang() const ;
    inline int numEntries() const ;
    inline std::string charset() const ;
    inline std::string filename() const ;
    
    //inline unsigned 	bgl_block_length_get(bgl_block obj);
    //inline char 	*bgl_block_data_get(bgl_block obj);
    //inline unsigned 	bgl_block_type_get(bgl_block obj);
    inline std::string 	bgl_entry_headword_get(bgl_entry obj);
    inline std::string 	bgl_entry_definition_get(bgl_entry obj);
    inline std::vector<std::string> bgl_entry_alternates_get(bgl_entry obj);

private:
  unsigned int bgl_readnum( int bytes );
  void convertToUtf8( std::string &s, int type );

    // from babylon.h
    unsigned int bgl_readnum( int );
    void convertToUtf8( std::string &, int = 0 );
    std::string m_filename;
    gzFile file;
    std::string m_title;
    std::string m_author;
    std::string m_email;
    std::string m_description;
    std::string m_copyright;
    std::string m_sourceLang;
    std::string m_targetLang;
    int m_numEntries;
    std::string m_defaultCharset;
    std::string m_sourceCharset;
    std::string m_targetCharset;

};

