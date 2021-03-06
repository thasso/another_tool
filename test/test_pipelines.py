#!/usr/bin/env python
from another.pipelines import Pipeline, PipelineTool
from another.tools import BashTool
import pytest


class SimpleTool(BashTool):
    pass


class Touch(BashTool):
    command = """touch ${name}"""
    inputs = {"name": None}
    outputs = {"file": "${name}"}


class Split(BashTool):
    command = """split ${file} ${count} ${prefix}"""
    inputs = {"file": None,
              "count": None,
              "prefix": None
              }
    outputs = {"files": lambda ctx: list(["%s-%d" % (ctx["prefix"], i) for i in range(ctx["count"])])}


def test_pipeline_tool_get_attribute_instance_vars():
    p = PipelineTool("pipeline", "tool", "tool")
    assert p._pipeline == "pipeline"
    assert p._tool == "tool"


def test_pipeline_tool_get_attribute_exception():
    p = PipelineTool("pipeline", BashTool(), "bash")
    with pytest.raises(AttributeError) as excinfo:
        p.unknown


def test_pipeline_tool_set_unknown_attribute():
    p = PipelineTool("pipeline", BashTool(), "bash")
    p.unknown = 1
    assert p.unknown.get() == 1
    assert p._kwargs["unknown"].value == 1


def test_split_tool_evaluation():
    s = Split()
    assert s.returns({"count": 2, "prefix": "test"}) == ["test-0", "test-1"]


def test_pipeline_adding_tools():
    p = Pipeline()
    touch = p.add(Touch())
    split = p.add(Split())
    assert len(p.tools) == 2
    assert p.tools["Touch"] == touch
    assert p.tools["Split"] == split


def test_pipeline_configure_tools():
    p = Pipeline()
    touch = p.add(Touch())
    split = p.add(Split())
    touch.name= "myfile.txt"
    split.file = touch.file
    split.prefix = "split"
    split.count = 2

    assert p.get_configuration(touch) == {"name": "myfile.txt", "file": "myfile.txt", "job": touch.job}
    assert p.get_configuration(split) == {"file": "myfile.txt",
                                    "prefix": "split",
                                    "count": 2,
                                          "files": ["split-0", "split-1"], "job": split.job}

def test_pipeline_dependencies():
    p = Pipeline()
    touch = p.add(Touch())
    split = p.add(Split())
    touch_b = p.add(Touch(), "b")
    touch_b.name = "myfile.txt"
    touch.name= touch_b.name
    split.file = touch.file
    split.prefix = "split"
    split.count = 2

    assert len(touch_b.get_dependencies()) == 0
    assert len(touch.get_dependencies()) == 1
    assert len(split.get_dependencies()) == 1
    assert list(split.get_dependencies()) == [touch]
    assert p.get_sorted_tools() == [touch_b, touch, split]
