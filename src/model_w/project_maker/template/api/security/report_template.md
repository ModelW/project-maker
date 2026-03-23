## System Description
&nbsp;

{tm.description}

&nbsp;

{tm.assumptions:if:

|Assumptions|
|-----------|
{tm.assumptions:repeat:|{{item}}| 
}

&nbsp;
&nbsp;
&nbsp;
}


## Dataflow Diagram - Level 0 DFD

![](cawl-dfd.png)

&nbsp;

## Dataflows
&nbsp;

Name|From|To |Data|Protocol|Port
|:----:|:----:|:---:|:----:|:--------:|:----:|
{dataflows:repeat:|{{item}}|{{item.source}}|{{item.sink}}|{{item.data}}|{{item.protocol}}|{{item.dstPort}}|
}

## Data Dictionary
&nbsp;

Name|Description|Classification
|:----:|:--------:|:----:|
{data:repeat:|{{item}}|{{item.description}}|{{item.classification}}|
}

&nbsp;

## Potential Threats

&nbsp;
&nbsp;

{findings:repeat:
<details>
  <summary>
    {{item.threat_id}} — {{item.description}}
  </summary>

  <h6>Targeted Element</h6>
  <p>{{item.target}}</p>

  <h6>Severity</h6>
  <p>{{item.severity}}</p>

  <h6>Mitigation</h6>
  <p>{{item.mitigations}}</p>

</details>
}||