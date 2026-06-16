<?php
  // model.json to labels.txt
  $data = json_decode(file_get_contents('model1.json'),true);
  $m=ARRAY();
  foreach($data as $k=>$v)
  {
    array_push($m,"{$k}"); //({$v['Chinese_Name']})
  }
  file_put_contents("labels.txt",implode("\n",$m));
  