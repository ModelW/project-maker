<style>
  b[class="Very High"] {{ color: #8b0000; font-weight: bold; backgroud-color: white;}}  
  b[class="High"] {{ color: #ff0000; font-weight: bold; backgroud-color: white;}}
  b[class="Medium"] {{ color: #ffa500; font-weight: bold; backgroud-color: white;}}
  b[class="Low"] {{ color: #0000ff; font-weight: bold; backgroud-color: white;}}
</style>

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

![Data Flow Diagram](dfd.png)

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

**Total Threats Identified:** {tm.threat_count}

&nbsp;
&nbsp;

{elements:repeat:{{item.findings:if:

### Element: {{item.name}}

{{item.findings:repeat:
<details>
  <summary>
    <b class="{{{{item.severity}}}}">[{{{{item.severity}}}}]</b> — {{{{item.id}}}}: {{{{item.description}}}}
  </summary>

    
    Targeted Element / Asset
    {{{{item.target}}}}

    Mitigation Strategy
    {{{{item.mitigations}}}}

    References & Standards
    {{{{item.references}}}}
    
</details>
<br/>
}}}}}||