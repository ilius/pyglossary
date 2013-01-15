//stardictbuilder.i
%module stardictbuilder
%include stl.i
%{
#include "stardictbuilder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <iostream>
%}

class StarDictBuilder{
public:
  StarDictBuilder( std::string filename );
  ~StarDictBuilder();
  bool addHeadword( std::string word, std::string def, std::string /*alternates*/ );
  bool finish();


// from stardictbuilder.h
  std::string filename();
  void setTitle( const std::string title );
  std::string title();
  void setAuthor( const std::string author );
  std::string author();
  void setLicense( const std::string license );
  std::string license();
  void setOrigLang( const std::string origLang );
  std::string origLang();
  void setDestLang( const std::string destLang );
  std::string destLang();
  void setDescription( const std::string description );
  std::string description();
  void setComments( const std::string comments );
  std::string comments();
  void setEmail( const std::string email );
  std::string email();
  void setWebsite( const std::string website );
  std::string website();
  void setVersion( const std::string version );
  std::string version();
  void setCreationDate( const std::string creationDate );
  std::string creationDate();
  void setLastUpdate( const std::string lastUpdate );
  std::string lastUpdate();
  void setMisc( const std::string misc );
  std::string misc();
  unsigned int headwords();
  unsigned int words();

protected:

  struct entry;

  typedef unsigned int uint32;
  typedef std::map<std::string, entry> dictionary;

  std::ofstream file;
  std::string m_ifofilename;
  std::string m_idxfilename;
  std::string m_dictfilename;

  // Header
  std::string m_title;
  std::string m_author;
  std::string m_license;
  std::string m_origLang;
  std::string m_destLang;
  uint32 m_entriescount;
  std::string m_description;
  std::string m_comments;
  std::string m_email;
  std::string m_website;
  std::string m_version;
  std::string m_creationDate;
  std::string m_lastUpdate;
  std::string m_misc;

  unsigned int m_size;
  bool m_isOk;

  uint32 m_wordcount;
  uint32 m_headerOffset;
  uint32 m_idxOffset;
  uint32 m_defOffset;

  std::string m_definition;

  dictionary dic;
};

