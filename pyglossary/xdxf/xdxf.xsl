<!-- Copyright (c) 2023 Saeed Rasooli -->
<!-- Copyright (c) 2016 ivan tkachenko me@ratijas.tk -->
<!-- Copyright (c) 2008-2011 Dmitry Zhuk. All rights reserved. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html"/>

  <xsl:template name="last-substring-after">
    <xsl:param name="text"/>
    <xsl:param name="separator"/>
    <xsl:variable name="tail" select="substring-after($text, $separator)"/>
    <xsl:choose>
      <xsl:when test="contains($tail, $separator)">
        <xsl:call-template name="last-substring-after">
          <xsl:with-param name="text" select="$tail"/>
          <xsl:with-param name="separator" select="$separator"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$tail" />
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="/">
    <div class="article">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="br">
    <br/>
  </xsl:template>

  <xsl:template match="i | b | sub | sup | tt | big | small">
    <xsl:element name="{name()}"><xsl:apply-templates/></xsl:element>
  </xsl:template>

  <xsl:template match="blockquote">
    <div class="m">
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="br[name(preceding-sibling::*[1])='blockquote' or name(following-sibling::*[1])='blockquote']" />

  <xsl:template match="tr">
    <span class="tr">[<xsl:apply-templates/>]</span>
  </xsl:template>

  <xsl:template match="k">
    <span class="k"><b><xsl:apply-templates/></b></span>
  </xsl:template>

  <xsl:template match="sr">
    <span class="sr"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="ex">
    <span class="example" style="padding: 10px 0px;"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="ex_orig">
    <i><xsl:apply-templates/></i>
  </xsl:template>

  <xsl:template match="ex_transl">
    <i><xsl:apply-templates/></i>
  </xsl:template>

  <xsl:template match="mrkd">
    <span class="mrkd"><b><xsl:apply-templates/></b></span>
  </xsl:template>

  <xsl:template match="pos | abr | abbr | gr">
    <span class="abr"><font color="green"><i><xsl:apply-templates/></i></font></span>
  </xsl:template>

  <xsl:template match="co">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="dtrn">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="c[@c]">
    <font color="{@c}"><xsl:apply-templates/></font>
  </xsl:template>

  <xsl:template match="c">
    <font color="green"><xsl:apply-templates/></font>
  </xsl:template>

  <xsl:template match="kref">
    <xsl:choose>
      <xsl:when test="@k">
        <a class="kref" href="bword://{@k}"><xsl:apply-templates/></a>
      </xsl:when>
      <xsl:otherwise>
        <a class="kref" href="bword://{text()}"><xsl:apply-templates/></a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="iref">
    <xsl:choose>
      <xsl:when test="@href">
        <a href="{@href}"><xsl:apply-templates/></a>
      </xsl:when>
      <xsl:otherwise>
        <a href="{text()}"><xsl:apply-templates/></a>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="rref">
    <xsl:variable name="ext">
      <xsl:call-template name="last-substring-after">
        <xsl:with-param name="text" select="text()"/>
        <xsl:with-param name="separator">.</xsl:with-param>
      </xsl:call-template>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="@type='image' or $ext='jpg' or $ext='png'">
        <img src="{text()}"/>
      </xsl:when>
      <xsl:when test="@type='sound' or $ext='wav' or $ext='mp3'">
        <a class="pr" href="audio:{text()}"><img style="width:25px;height:22px;" src="res:///sound.png"/></a>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="categ">
    <span class="category" style="background-color: green;"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="opt">
    (<xsl:apply-templates/>)
  </xsl:template>

  <!-- http://stackoverflow.com/questions/3309746/how-to-convert-newline-into-br-with-xslt -->
  <xsl:template match="text()" name="insertBreaks">
    <xsl:param name="pText" select="."/>

    <xsl:choose>
      <xsl:when test="not(contains($pText, '&#xA;'))">
        <xsl:copy-of select="$pText"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="substring-before($pText, '&#xA;')"/>
        <br/>
        <xsl:call-template name="insertBreaks">
          <xsl:with-param name="pText" select=
                  "substring-after($pText, '&#xA;')"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
