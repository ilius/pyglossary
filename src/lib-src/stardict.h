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
 *   GNU General Public License for more details.                          *
 *                                                                         *
 *   You should have received a copy of the GNU General Public License     *
 *   along with this program; if not, write to the                         *
 *   Free Software Foundation, Inc.,                                       *
 *   51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.          *
 ***************************************************************************/
#ifndef STARDICT_H
#define STARDICT_H

//#include <string>
#include <cstring>
#include <stdlib.h>
#include <fstream>
#include <vector>

using namespace std;

/**
@author Raul Fernandes
*/
class StarDict{
public:
    StarDict( const char* );

    ~StarDict();

    inline bool extraField() const { return m_extraField; };
    inline bool hasName() const { return m_hasName; };
    inline unsigned long mtime() const  { return m_mtime; };
    inline const char* filename() const { return m_filename.c_str(); };
    const char* search( const char* );
    inline int size() const { return m_wordcount; };
    inline bool isOk() const { return m_isOk; };
    inline const char* bookname() const { return m_bookname.c_str(); };
    inline const char* author() const { return m_author.c_str(); };
    inline const char* version() const { return m_version.c_str(); };
    inline const char* description() const { return m_description.c_str(); };
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

#endif // STARDICT_H
