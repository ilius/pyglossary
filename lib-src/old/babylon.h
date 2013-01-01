/***************************************************************************
 *   Copyright (C) 2007 by Raul Fernandes and Karl Grill                   *
 *   rgbr@yahoo.com.br                                                     *
 *   Edited by Saeed Rasooli <saeed.gnu@gmail.com> at 2008-2009            *
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

#ifndef BABYLON_H
#define BABYLON_H

#include <stdlib.h>
#include <zlib.h>
#include <memory.h>

#include <string> 
#include <vector>

const std::string bgl_language[] = {
	"English", 
	"French",
	"Italian",
	"Spanish",
	"Dutch",
	"Portuguese",
	"German",
	"Russian",
	"Japanese",
	"Traditional Chinese",
	"Simplified Chinese",
	"Greek",
	"Korean",
	"Turkish",
	"Hebrew",
	"Arabic",
	"Thai",
	"Other",
	"Other Simplified Chinese dialects",
	"Other Traditional Chinese dialects",
	"Other Eastern-European languages",
	"Other Western-European languages",
	"Other Russian languages",
	"Other Japanese languages",
	"Other Baltic languages",
	"Other Greek languages",
	"Other Korean dialects",
	"Other Turkish dialects",
	"Other Thai dialects",
	"Polish",
	"Hungarian",
	"Czech",
	"Lithuanian",
	"Latvian",
	"Catalan",
	"Croatian",
	"Serbian",
	"Slovak",
	"Albanian",
	"Urdu",
	"Slovenian",
	"Estonian",
	"Bulgarian",
	"Danish",
	"Finnish",
	"Icelandic",
	"Norwegian",
	"Romanian",
	"Swedish",
	"Ukrainian",
	"Belarusian",
	"Farsi",
	"Basque",
	"Macedonian",
	"Afrikaans",
	"Faeroese",
	"Latin",
	"Esperanto",
	"Tamazight",
	"Armenian"};


const std::string bgl_charsetname[] = {
	"Default" ,
	"Latin",
	"Eastern European",
	"Cyrillic",
	"Japanese",
	"Traditional Chinese",
	"Simplified Chinese",
	"Baltic",
	"Greek",
	"Korean",
	"Turkish",
	"Hebrew",
	"Arabic",
	"Thai" };

const std::string bgl_charset[] = {
	"ISO-8859-1", /*Default*/
	"ISO-8859-1", /*Latin*/
	"ISO-8859-2", /*Eastern European*/
	"ISO-8859-5", /*Cyriilic*/
	"ISO-8859-14", /*Japanese*/
	"ISO-8859-14", /*Traditional Chinese*/
	"ISO-8859-15", /*Simplified Chinese*/
	"CP1257", /*Baltic*/
	"CP1253", /*Greek*/
	"ISO-8859-15",  /*Korean*/
	"ISO-8859-9", /*Turkish*/
	"ISO-8859-9", /*Hebrew*/
	"CP1256", /*Arabic*/
	"CP874"  /*Thai*/ };

const std::string partOfSpeech[] = {
  "n.",
  "adj.",
  "v.",
  "adv.",
  "interj.",
  "pron.",
  "prep.",
  "conj.",
  "suff.",
  "pref.",
  "art." };

typedef struct {
	unsigned type;
	unsigned length;
	char * data;
} bgl_block;

typedef struct {
        std::string headword;
        std::string definition;
        std::vector<std::string> alternates;
} bgl_entry;





class Babylon
{
public:
    Babylon( std::string );
    ~Babylon();

    bool open();
    void close();
    bool readBlock( bgl_block& );
    bool read();
    bgl_entry readEntry();

    inline std::string title() const { return m_title; };
    inline std::string author() const { return m_author; };
    inline std::string email() const { return m_email; };
    inline std::string description() const { return m_description; };
    inline std::string copyright() const { return m_copyright; };
    inline std::string sourceLang() const { return m_sourceLang; };
    inline std::string targetLang() const { return m_targetLang; };
    inline int numEntries() const { return m_numEntries; };
    inline std::string charset() const { return m_defaultCharset; };

    inline std::string filename() const { return m_filename; };

    //inline unsigned 	bgl_block_length_get(bgl_block obj){return obj.length;}
    //inline char 	*bgl_block_data_get(bgl_block obj){return obj.data;}
    //inline unsigned 	bgl_block_type_get(bgl_block obj){return obj.type;}
    inline std::string 	bgl_entry_headword_get(bgl_entry obj){return obj.headword;}
    inline std::string 	bgl_entry_definition_get(bgl_entry obj){return obj.definition;}
    inline std::vector<std::string> bgl_entry_alternates_get(bgl_entry obj){return obj.alternates;}




private:
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

    enum CHARSET { DEFAULT_CHARSET, SOURCE_CHARSET, TARGET_CHARSET };
};

#endif // BABYLON_H
