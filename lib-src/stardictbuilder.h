/***************************************************************************
 *   Copyright (C) 2007 by Raul Fernandes                                  *
 *   rgbr@yahoo.com.br                                                     *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.          *
 ***************************************************************************/
#ifndef STARDICTBUILDER_H
#define STARDICTBUILDER_H

#include "dictbuilder.h"

#include <map>
#include <fstream>

class StarDictBuilder : public DictBuilder
{

public:
  StarDictBuilder( std::string filename );
  ~StarDictBuilder();

  bool addHeadword( std::string word, std::string def, std::string alternates = std::string() );
  bool finish();

  std::string filename() { return m_ifofilename; };
  void setTitle( const std::string title ) { m_title = title; };
  std::string title() { return m_title; };
  void setAuthor( const std::string author ) { m_author = author; };
  std::string author() { return m_author; };
  void setLicense( const std::string license ) { m_license = license; };
  std::string license() { return m_license; };
  void setOrigLang( const std::string origLang ) { m_origLang = origLang; };
  std::string origLang() { return m_origLang; };
  void setDestLang( const std::string destLang ) { m_destLang = destLang; };
  std::string destLang() { return m_destLang; };
  void setDescription( const std::string description ) { m_description = description; };
  std::string description() { return m_description; };
  void setComments( const std::string comments ) { m_comments = comments; };
  std::string comments() { return m_comments; };
  void setEmail( const std::string email ) { m_email = email; };
  std::string email() { return m_email; };
  void setWebsite( const std::string website ) { m_website = website; };
  std::string website() { return m_website; };
  void setVersion( const std::string version ) { m_version = version; };
  std::string version() { return m_version; };
  void setCreationDate( const std::string creationDate ) { m_creationDate = creationDate; };
  std::string creationDate() { return m_creationDate; };
  void setLastUpdate( const std::string lastUpdate ) { m_lastUpdate = lastUpdate; };
  std::string lastUpdate() { return m_lastUpdate; };
  void setMisc( const std::string misc ) { m_misc = misc; };
  std::string misc() { return m_misc; };
  unsigned int headwords() { return m_entriescount; };
  unsigned int words() { return m_wordcount; };

protected:

  struct entry {
    unsigned long position;
    unsigned long size;
  };

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

#endif // STARDICTBUILDER_H
