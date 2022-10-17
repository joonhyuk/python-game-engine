<?xml version="1.0" encoding="UTF-8"?>
<tileset version="1.9" tiledversion="1.9.2" name="test_fan_blade" tilewidth="162" tileheight="160" tilecount="4" columns="0">
 <grid orientation="orthogonal" width="1" height="1"/>
 <tile id="0">
  <image width="162" height="150" source="../resources/art/test_fan_blade0.png"/>
 </tile>
 <tile id="1">
  <image width="160" height="160" source="../resources/art/test_fan_blade2.png"/>
 </tile>
 <tile id="2">
  <image width="128" height="128" source="../resources/art/test_fan_blade3.png"/>
 </tile>
 <tile id="3" class="DynamicFan">
  <properties>
   <property name="angle" type="float" value="90"/>
   <property name="hit_box_algorithm" propertytype="hit_box_algorithm" value="Detailed"/>
  </properties>
  <image width="122" height="122" source="../resources/art/test_fan_blade4.png"/>
 </tile>
</tileset>
