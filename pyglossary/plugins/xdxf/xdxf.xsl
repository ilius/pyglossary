<!-- Copyright (c) 2008-2011 Dmitry Zhuk. All rights reserved. -->
<!-- Modified by Ratijas. -->
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

  <xsl:template match="k | ex">
    <span class="{name()}"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="pos | abr">
    <span class="abr"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="c[@c]">
    <span style="color:{@c}"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="c">
    <span style="color: green"><xsl:apply-templates/></span>
  </xsl:template>

  <xsl:template match="dtrn | co">
    <xsl:apply-templates/>
  </xsl:template>

  <xsl:template match="kref">
    <xsl:choose>
      <xsl:when test="@k">
        <a class="kref" href="{@k}"><xsl:apply-templates/></a>
      </xsl:when>
      <xsl:otherwise>
        <a class="kref" href="{text()}"><xsl:apply-templates/></a>
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

</xsl:stylesheet>