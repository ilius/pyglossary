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

#include "stardictbuilder.h"

#include <iostream>

StarDictBuilder::StarDictBuilder( std::string filename )
{
  m_ifofilename = filename;
  m_idxfilename = filename;
  m_idxfilename = m_idxfilename.substr( 0, m_idxfilename.length() - 4 ) + ".idx";
  m_dictfilename = filename;
  m_dictfilename = m_dictfilename.substr( 0, m_dictfilename.length() - 4 ) + ".dict";
  m_entriescount = 0;
}


StarDictBuilder::~StarDictBuilder()
{
}

bool StarDictBuilder::addHeadword( std::string word, std::string def, std::string /*alternates*/ )
{
  m_entriescount++;
  struct entry entry;
  std::string definition = def;
  entry.position = m_definition.length();
  entry.size = definition.length();
  std::string headword;

  headword = word;
  dic.insert( make_pair( headword, entry ) );

  // TODO: syn file
  /*
  // Alternate forms
  std::vector<std::string>::iterator iter;
  for(iter = alternates.begin();iter != alternates.end(); iter++)
  {
    dic.insert( make_pair( *iter, entry ) );
  }*/

  m_definition += definition;
  return true;
}

bool StarDictBuilder::finish()
{
  m_wordcount = dic.size();


  //////////////////
  // Idx file
  /////////////////

  file.open( m_idxfilename.c_str() );
  if( !file.is_open() )
  {
    return false;
  }

  dictionary::iterator iter;
  for( iter = dic.begin(); iter != dic.end(); ++iter ) {
    file.write( iter->first.data(), iter->first.length() );
    file.put( '\0' );
    file.put( (iter->second.position & 0xff000000 ) >> 24 );
    file.put( (iter->second.position & 0x00ff0000 ) >> 16 );
    file.put( (iter->second.position & 0x0000ff00 ) >> 8 );
    file.put( iter->second.position & 0x000000ff );
    file.put( (iter->second.size & 0xff000000 ) >> 24 );
    file.put( (iter->second.size & 0x00ff0000 ) >> 16 );
    file.put( (iter->second.size & 0x0000ff00 ) >> 8 );
    file.put( iter->second.size & 0x000000ff );
    //std::cout << "Headword: " << iter->first.c_str() << " - Position: " << iter->second.position << " - Size: " << iter->second.size <<  std::endl;
  }
  unsigned int idxfilesize = file.tellp();
  file.close();


  //////////////////
  // Ifo file
  /////////////////

  file.open( m_ifofilename.c_str() );
  if( !file.is_open() )
  {
    return false;
  }

  char buf[1024];
  sprintf( buf, "StarDict's dict ifo file\nversion=2.4.2\nbookname=%s\nwordcount=%d\nidxfilesize=%d\nsametypesequence=m\n", m_title.c_str(), m_wordcount, idxfilesize );
  std::string line;
  line = buf;
  if( m_author.size() > 0 ) line += "author=" + m_author  + '\n';
  if( m_email.size() > 0 ) line += "email=" + m_email + '\n';
  if( m_website.size() > 0 ) line += "website=" + m_website + '\n';
  if( m_description.size() > 0 ) line += "description=" + m_description + '\n';
  //TODO: line += "date=" + '\n';

  file.write( line.data(), line.length() );
  file.close();


  //////////////////
  // Dict file
  /////////////////

  file.open( m_dictfilename.c_str() );
  if( !file.is_open() )
  {
    return false;
  }
  file.write( m_definition.data(), m_definition.length() );
  file.close();

  return true;
}
