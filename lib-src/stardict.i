//stardict.i
%module stardict
%include stl.i
%{
#include "stardict.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iconv.h>
#include <zlib.h>
%}

class StarDict{
public:
    StarDict( const char* );

    ~StarDict();

    inline bool extraField() const;
    inline bool hasName() const;
    inline unsigned long mtime() const ;
    inline const char* filename() const;
    const char* search( const char* );
    inline int size() const ;
    inline bool isOk() const ;
    inline const char* bookname() const ;
    inline const char* author() const ;
    inline const char* version() const ;
    inline const char* description() const ;
    vector<string> dump();


protected:
    string Inflate( const string & );

    void readExtraField();
    void readFileName();
    void readComment();

    bool m_isOk;

    bool isCompressed;
    bool isIdxCompressed;
    ifstream file;
    string dictFileName;
    string idxFileName;
    string ifoFileName;
    bool m_extraField;
    bool m_hasName;
    bool FTEXT; // bit 0 - � texto
    bool FHCRC; // bit 1 - tem CRC16
    bool FCOMMENT; // bit 3 - tem coment�rio
    unsigned long m_mtime;
    unsigned long XLEN;
    char SI1, SI2;
    unsigned long LEN, VER, CHLEN, CHCNT;
    vector<unsigned long> offsets;
    string m_comment;
    string m_filename;
    char *crc16[2];
    unsigned long offset;

    // ifo file
    string m_version;
    string m_bookname;
    unsigned int m_wordcount;
    unsigned long m_idxfilesize;
    string m_sametypesequence;
    string m_author;
    string m_email;
    string m_website;
    string m_description;
    string m_date;

    struct entry {
      string headword;
      unsigned long position;
      unsigned long size;
    };
};
/*
%extend StarDict{
  public:
  std::string vector_get_item(vector<string> v, int i){
    //try{
      return v[i];
    //}excpet(){
    //  return '';
    //};
  };
  int vector_get_size(vector<string> v){
    return v.size();
  };
};
*/

