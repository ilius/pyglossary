/***************************************************************************
 *   Copyright (C) 2005-2007 by Raul Fernandes                             *
 *   rgfbr@yahoo.com.br                                                    *
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 *   This program is distributed in the hope that it will be useful,       *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU General Public License for more details.                         *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.          *
 ***************************************************************************/
#include "stardict.h"

#include <zlib.h>

#define CHUNK 0xffffL

StarDict::StarDict( const char *filename )
{
  ifoFileName = filename;
  idxFileName = filename;
  idxFileName.replace( idxFileName.size() - 4, 4, ".idx" );
  dictFileName = filename;
  dictFileName.replace( dictFileName.size() - 4, 4, ".dict" );

  // Ifo file
  file.open( ifoFileName.c_str() );
  if( !file.is_open() )
  {
    m_isOk = false;
    return;
  }

  // Read the ifo file
  string ifoline;
  while( !file.eof() )
  {
    getline( file, ifoline );
    if( ifoline.find( "=" ) == string::npos ) continue;
    if( ifoline.find( '\n' ) != string::npos ) ifoline.erase( ifoline.size() - 1 );
    if( ifoline.find( "version=" ) != string::npos ) m_version = ifoline.substr( 8 );
    if( ifoline.find( "bookname=" ) != string::npos ) m_bookname = ifoline.substr( 9 );
    if( ifoline.find( "sametypesequence=" ) != string::npos ) m_sametypesequence = ifoline.substr( 17 );
    if( ifoline.find( "idxfilesize=" ) != string::npos ) m_idxfilesize = atoi( ifoline.substr( 12 ).c_str() );
    if( ifoline.find( "wordcount=" ) != string::npos ) m_wordcount = atoi( ifoline.substr( 10 ).c_str() );
    if( ifoline.find( "author=" ) != string::npos ) m_author = ifoline.substr( 7 );
    if( ifoline.find( "email=" ) != string::npos ) m_email = ifoline.substr( 6 );
    if( ifoline.find( "website=" ) != string::npos ) m_website = ifoline.substr( 8 );
    if( ifoline.find( "description=" ) != string::npos ) m_description = ifoline.substr( 12 );
    if( ifoline.find( "date=" ) != string::npos ) m_date = ifoline.substr( 5 );
  }
  file.close();
  if( m_sametypesequence != "m" )
  {
    // This class only support sametypesequence == "m" for now
    m_isOk = false;
    //cout << "Dictionary not loaded. Stardict plugin supports only sametypesequence == \"m\"" << endl;
    return;
  }

  // Index file
  // it should be on the same directory that ifo file
  file.open( idxFileName.c_str() );
  if( !file.is_open() )
  {
    idxFileName += ".gz";
    file.open( idxFileName.c_str() );
    if( !file.is_open() )
    {
      m_isOk = false;
      return;
    }
    isIdxCompressed = true;
    file.close();
  }else{
    isIdxCompressed = false;
    file.close();
  }

  // Definition file (.dict)
  // it should be on the same directory that index file
  // Checks if the definition file is compressed or not
  file.open( dictFileName.c_str() );
  if( !file.is_open() )
  {
    dictFileName += ".dz";
    file.open( dictFileName.c_str() );
    if( !file.is_open() )
    {
      m_isOk = false;
      return;
    }
    // The definition file is compressed (.dict.dz)
    // Read the header
    isCompressed = true;

    char header[12];
    file.readsome( header, 12 );

    if( header[0] != '\x1f' || header[1] != '\x8b' ) //ID1 = 31 (0x1f, \037) ID2 = 139 (0x8b, \213)
    {
      m_isOk = false;
      return;
    }
    //header[2] // COMPRESSION
    FTEXT = header[3] & 1;
    FHCRC = header[3] & 2;
    m_extraField = header[3] & 4;
    m_hasName = header[3] & 8;
    FCOMMENT = header[3] & 16;
    m_mtime = (unsigned char)header[4] | (unsigned char)header[5] << 8 + (unsigned char)header[6] << 16 + (unsigned char)header[7] << 24;
    //header[8] // Compression type
    //header[9] // Operating System
    // If has extra field, read it
    if( m_extraField )
    {
      XLEN = (unsigned char)header[10] | (unsigned char)header[11] << 8;
      readExtraField();
    }
    // If has name of decompressed file, read it
    if( m_hasName )
    {
      readFileName();
    }
    // If has a comment field, read it
    if( FCOMMENT )
    {
      readFileName();
    }
    // If has a CRC field, read it
    if( FHCRC )
    {
      *crc16[0] = file.get();
      *crc16[1] = file.get();
    }
    // Get the current position
    // This is start position of the chunks of compressed data
    offset = file.tellg();
    file.close();
  }else{
    isCompressed = false;
    file.close();
  }
  m_isOk = true;
}


StarDict::~StarDict()
{
}




/*!
    \fn StarDict::readExtraField()
 */
void StarDict::readExtraField()
{
  char buf[10];
  offsets.clear();

  file.readsome( buf, 10 );

  SI1 = buf[0];
  SI2 = buf[1];
  // length of the subfield data
  LEN = (unsigned char)buf[2] | (unsigned char)buf[3] << 8;
  int size = (int)LEN - 6;
  // Version
  VER = (unsigned char)buf[4] | (unsigned char)buf[5] << 8;
  // length of a "chunk" of data
  CHLEN = (unsigned char)buf[6] | (unsigned char)buf[7] << 8;
  // how many chunks are preset
  CHCNT = (unsigned char)buf[8] | (unsigned char)buf[9] << 8;

  unsigned long data;
  char table[size];
  offsets.reserve( size );
  file.readsome( table, size );

  for(int a = 0; a < size; a++)
  {
    // how long each chunk is after compression
    data = (unsigned char)table[a] | (unsigned char)table[a+1] << 8;
    a++;
    offsets.push_back( data );
  }
}


/*!
    \fn StarDict::readFileName()
 */
void StarDict::readFileName()
{
  string filename;
  char byte;
  byte = file.get();
  while( byte != '\0' )
  {
    filename += byte;
    byte = file.get();
  }
  m_filename = filename;
}


/*!
    \fn StarDict::readComment()
 */
void StarDict::readComment()
{
  string comment;
  char byte;
  byte = file.get();
  while( byte != '\0' )
  {
    comment += byte;
    byte = file.get();
  }
  m_comment = comment;
}


/*!
    \fn StarDict::search( const char *word )
 */
const char* StarDict::search( const char *word )
{
  char line[256];
  string headword;
  struct entry entry;
  bool found = false;
  uint a;
  string idxFile;

  char buf[m_idxfilesize];
  if( isIdxCompressed ) {
    gzFile gzfile = gzopen( idxFileName.c_str(), "rb" );
    if( gzfile == NULL ) {
      m_isOk = false;
      return "";
    }
    int read = gzread( gzfile, buf, m_idxfilesize );
    if( m_idxfilesize != (uint)read ) {
      m_isOk = false;
      return "";
    }
    idxFile.assign( buf, m_idxfilesize );
    gzclose( gzfile );
  }else{
    ifstream file;
    file.open( idxFileName.c_str() );
    file.readsome( buf, m_idxfilesize );
    idxFile.assign( buf, m_idxfilesize );
    file.close();
  }

  // Find the headword in index file
  uint pos = 0;
  for(uint b=0;b<m_wordcount;b++)
  {
    a = 0;
    do
    {
      line[a] = idxFile[pos];
      a++;
      pos++;
    }while( line[a-1] != '\0' );

    headword = line;

    for(a=0;a<8;a++) line[a] = idxFile[pos++];

    if( headword.compare( word ) != 0 ) continue;

    found = true;

    entry.headword = headword;

    // Get the position of definition in definition file
    entry.position = (unsigned char)line[3] | (unsigned char)line[2] << 8 | (unsigned char)line[1] << 16 | (unsigned char)line[0] << 24;

    // Get the size of definition in definition file
    entry.size = (unsigned char)line[7] | (unsigned char)line[6] << 8 | (unsigned char)line[5] << 16 | (unsigned char)line[4] << 24;

  }

  // If not found, return a null string
  if( !found ) return "";

  // Check if the definition file is compressed
  if( isCompressed )
  {
    // Calculate how many chunks we have to skip
    uint startChunk = entry.position / CHLEN ;
    uint endChunk = (entry.position + entry.size ) / CHLEN;

    // Calculate the position of definition in chunk
    uint pos = entry.position % CHLEN;

    // Size of the chunk we are looking for
    unsigned long chunkLen = 0;
    for(uint a = startChunk; a < endChunk + 1; a++ ) chunkLen += offsets[a];

    // How many bytes we have to skip
    unsigned long skip = 0;
    for(uint a=0;a<startChunk;a++) skip += offsets[a];

    // Definition file
    file.open( dictFileName.c_str() );

    // Jump to chunk we are looking for
    file.seekg( offset + skip );

    // Get the compressed data
    char buf[chunkLen];
    file.readsome( buf, chunkLen );
    string data( buf, chunkLen );
    file.close();

    // Decompress the data
    string result = Inflate( data );

    // Returns only the definition
    return result.substr( pos, entry.size ).c_str();
  }else{
    // The file is not compressed
    file.open( dictFileName.c_str() );

    // Jump to position of definition
    file.seekg( entry.position );

    // Get the definition
    char buf[entry.size];
    file.readsome( buf, entry.size );
    string result( buf, entry.size );
    file.close();

    // Return the result
    return result.c_str();
  }
  return "";
}


string StarDict::Inflate( const string &data )
{
    //cout<< "Inflate()" << endl;
    int ret;
    z_stream strm;
    char out[CHUNK];
    string result;
    result.reserve( 65536 );

    // Inicialization of zlib
    strm.zalloc = Z_NULL;
    strm.zfree = Z_NULL;
    strm.opaque = Z_NULL;
    strm.avail_in = 0;
    strm.next_in = Z_NULL;
    ret = inflateInit2( &strm, -MAX_WBITS );
    if (ret != Z_OK)
      return "";

      // Compressed data
      strm.avail_in = data.size();
      strm.next_in = (Bytef*)data.data();

      /* run inflate() on input until output buffer not full */
      do {
        strm.avail_out = CHUNK;
        strm.next_out = (Bytef*)out;
        ret = inflate(&strm, Z_SYNC_FLUSH);
        switch (ret) {
          case Z_NEED_DICT:
            ret = Z_DATA_ERROR;     /* and fall through */
          case Z_DATA_ERROR:
          case Z_MEM_ERROR:
            (void)inflateEnd(&strm);
            return ""; // Error
        }
        result += out;
      } while (strm.avail_out == 0);

    /* clean up and return */
    ret = inflateEnd(&strm);
    return result;
}


std::vector<std::string> StarDict::dump()
{
  char line[256];
  string headword;
  struct entry entry;
  bool found = false;
  uint a;
  string idxFile;
  vector<string> list;

  char buf[m_idxfilesize];
  if( isIdxCompressed ) {
    gzFile gzfile = gzopen( idxFileName.c_str(), "rb" );
    if( gzfile == NULL ) {
      m_isOk = false;
      return vector<string>();
    }
    int read = gzread( gzfile, buf, m_idxfilesize );
    if( m_idxfilesize != (uint)read ) {
      m_isOk = false;
      return vector<string>();
    }
    idxFile.assign( buf, m_idxfilesize );
    gzclose( gzfile );
  }else{
    ifstream file;
    file.open( idxFileName.c_str() );
    file.readsome( buf, m_idxfilesize );
    idxFile.assign( buf, m_idxfilesize );
    file.close();
  }

  // Find the headword in index file
  uint pos = 0;
  list.reserve( m_wordcount );
  for(uint b=0;b<m_wordcount;b++)
  {
    a = 0;
    do
    {
      line[a] = idxFile[pos];
      a++;
      pos++;
    }while( line[a-1] != '\0' );

    headword = line;

    for(a=0;a<8;a++) line[a] = idxFile[pos++];

    list.push_back( headword );
  }
  return list;
}
