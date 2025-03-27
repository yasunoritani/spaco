#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPACO - 構造レベルのテスト

このモジュールは、構造レベルの表現クラスのテストを提供します。
"""

import unittest
import json
from src.language_processor.representation.base import ValidationError
from src.language_processor.representation.structure_level import StructureLevel, StructureComponent, StructureType


class TestStructureComponent(unittest.TestCase):
    """構造構成要素クラスのテスト"""
    
    def test_init(self):
        """構造構成要素の初期化のテスト"""
        component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0}, {"source": "template"})
        self.assertEqual(component.component_type, "oscillator")
        self.assertEqual(component.name, "main_osc")
        self.assertEqual(component.value, {"type": "sine", "frequency": 440.0})
        self.assertEqual(component.metadata, {"source": "template"})
    
    def test_validate(self):
        """構造構成要素の検証のテスト"""
        # 有効な構成要素
        component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        self.assertTrue(component.validate())
        
        # 無効な構成要素（種類が空）
        with self.assertRaises(ValidationError):
            component = StructureComponent("", "main_osc", {"type": "sine"})
            component.validate()
        
        # 無効な構成要素（名前が空）
        with self.assertRaises(ValidationError):
            component = StructureComponent("oscillator", "", {"type": "sine"})
            component.validate()
        
        # 無効な構成要素（値がNone）
        with self.assertRaises(ValidationError):
            component = StructureComponent("oscillator", "main_osc", None)
            component.validate()
    
    def test_to_dict(self):
        """構造構成要素の辞書変換のテスト"""
        component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0}, {"source": "template"})
        component_dict = component.to_dict()
        
        self.assertEqual(component_dict["component_type"], "oscillator")
        self.assertEqual(component_dict["name"], "main_osc")
        self.assertEqual(component_dict["value"], {"type": "sine", "frequency": 440.0})
        self.assertEqual(component_dict["metadata"], {"source": "template"})
    
    def test_from_dict(self):
        """構造構成要素の辞書からの生成のテスト"""
        component_dict = {
            "component_type": "oscillator",
            "name": "main_osc",
            "value": {"type": "sine", "frequency": 440.0},
            "metadata": {"source": "template"}
        }
        
        component = StructureComponent.from_dict(component_dict)
        
        self.assertEqual(component.component_type, "oscillator")
        self.assertEqual(component.name, "main_osc")
        self.assertEqual(component.value, {"type": "sine", "frequency": 440.0})
        self.assertEqual(component.metadata, {"source": "template"})


class TestStructureLevel(unittest.TestCase):
    """構造レベルの表現クラスのテスト"""
    
    def test_init(self):
        """構造レベルの初期化のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        env_component = StructureComponent("envelope", "main_env", {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5})
        
        components = {
            "main_osc": osc_component,
            "main_env": env_component
        }
        
        connections = [("main_osc", "main_env")]
        source_parameters = ["frequency", "amplitude", "attack", "decay", "sustain", "release"]
        metadata = {"template_name": "basic_synth"}
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components, connections, source_parameters, metadata)
        
        self.assertEqual(structure.structure_type, StructureType.SYNTH_DEF)
        self.assertEqual(structure.components, components)
        self.assertEqual(structure.connections, connections)
        self.assertEqual(structure.source_parameters, source_parameters)
        self.assertEqual(structure.metadata, metadata)
    
    def test_validate(self):
        """構造レベルの検証のテスト"""
        # 有効な構造
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        env_component = StructureComponent("envelope", "main_env", {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5})
        
        components = {
            "main_osc": osc_component,
            "main_env": env_component
        }
        
        connections = [("main_osc", "main_env")]
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components, connections)
        self.assertTrue(structure.validate())
        
        # 無効な構造（タイプがNone）
        with self.assertRaises(ValidationError):
            structure = StructureLevel(None, components, connections)
            structure.validate()
        
        # 無効な構造（構成要素がない）
        with self.assertRaises(ValidationError):
            structure = StructureLevel(StructureType.SYNTH_DEF, {}, connections)
            structure.validate()
        
        # 無効な構造（無効な構成要素）
        invalid_component = StructureComponent("oscillator", "", {"type": "sine"})  # 名前が空
        components = {"invalid": invalid_component}
        with self.assertRaises(ValidationError):
            structure = StructureLevel(StructureType.SYNTH_DEF, components, connections)
            structure.validate()
        
        # 無効な構造（存在しない構成要素への接続）
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        components = {"main_osc": osc_component}
        connections = [("main_osc", "non_existent")]
        with self.assertRaises(ValidationError):
            structure = StructureLevel(StructureType.SYNTH_DEF, components, connections)
            structure.validate()
    
    def test_to_dict(self):
        """構造レベルの辞書変換のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        env_component = StructureComponent("envelope", "main_env", {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5})
        
        components = {
            "main_osc": osc_component,
            "main_env": env_component
        }
        
        connections = [("main_osc", "main_env")]
        source_parameters = ["frequency", "amplitude", "attack", "decay", "sustain", "release"]
        metadata = {"template_name": "basic_synth"}
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components, connections, source_parameters, metadata)
        structure_dict = structure.to_dict()
        
        self.assertEqual(structure_dict["structure_type"], "SYNTH_DEF")
        self.assertEqual(structure_dict["connections"], connections)
        self.assertEqual(structure_dict["source_parameters"], source_parameters)
        self.assertEqual(structure_dict["metadata"], metadata)
        self.assertEqual(structure_dict["components"]["main_osc"]["component_type"], "oscillator")
        self.assertEqual(structure_dict["components"]["main_env"]["component_type"], "envelope")
    
    def test_from_dict(self):
        """構造レベルの辞書からの生成のテスト"""
        structure_dict = {
            "structure_type": "SYNTH_DEF",
            "components": {
                "main_osc": {
                    "component_type": "oscillator",
                    "name": "main_osc",
                    "value": {"type": "sine", "frequency": 440.0}
                },
                "main_env": {
                    "component_type": "envelope",
                    "name": "main_env",
                    "value": {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5}
                }
            },
            "connections": [["main_osc", "main_env"]],
            "source_parameters": ["frequency", "amplitude", "attack", "decay", "sustain", "release"],
            "metadata": {"template_name": "basic_synth"}
        }
        
        structure = StructureLevel.from_dict(structure_dict)
        
        self.assertEqual(structure.structure_type, StructureType.SYNTH_DEF)
        self.assertEqual(structure.connections, [["main_osc", "main_env"]])
        self.assertEqual(structure.source_parameters, ["frequency", "amplitude", "attack", "decay", "sustain", "release"])
        self.assertEqual(structure.metadata, {"template_name": "basic_synth"})
        self.assertEqual(structure.components["main_osc"].component_type, "oscillator")
        self.assertEqual(structure.components["main_env"].component_type, "envelope")
    
    def test_add_component(self):
        """構成要素の追加のテスト"""
        structure = StructureLevel(StructureType.SYNTH_DEF)
        
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        structure.add_component("main_osc", osc_component)
        
        self.assertTrue(structure.has_component("main_osc"))
        self.assertEqual(structure.get_component("main_osc"), osc_component)
    
    def test_add_connection(self):
        """接続の追加のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        env_component = StructureComponent("envelope", "main_env", {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5})
        
        components = {
            "main_osc": osc_component,
            "main_env": env_component
        }
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components)
        structure.add_connection("main_osc", "main_env")
        
        self.assertEqual(structure.connections, [("main_osc", "main_env")])
    
    def test_get_component(self):
        """構成要素の取得のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        structure = StructureLevel(StructureType.SYNTH_DEF, {"main_osc": osc_component})
        
        self.assertEqual(structure.get_component("main_osc"), osc_component)
        self.assertIsNone(structure.get_component("unknown"))
    
    def test_has_component(self):
        """構成要素の存在確認のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        structure = StructureLevel(StructureType.SYNTH_DEF, {"main_osc": osc_component})
        
        self.assertTrue(structure.has_component("main_osc"))
        self.assertFalse(structure.has_component("unknown"))
    
    def test_get_component_names(self):
        """構成要素名の取得のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        env_component = StructureComponent("envelope", "main_env", {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5})
        
        components = {
            "main_osc": osc_component,
            "main_env": env_component
        }
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components)
        
        self.assertEqual(structure.get_component_names(), {"main_osc", "main_env"})
    
    def test_get_connections_to(self):
        """入力への接続の取得のテスト"""
        osc1_component = StructureComponent("oscillator", "osc1", {"type": "sine", "frequency": 440.0})
        osc2_component = StructureComponent("oscillator", "osc2", {"type": "saw", "frequency": 220.0})
        mixer_component = StructureComponent("mixer", "mixer", {"type": "mix"})
        
        components = {
            "osc1": osc1_component,
            "osc2": osc2_component,
            "mixer": mixer_component
        }
        
        connections = [("osc1", "mixer"), ("osc2", "mixer")]
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components, connections)
        
        self.assertEqual(structure.get_connections_to("mixer"), ["osc1", "osc2"])
        self.assertEqual(structure.get_connections_to("osc1"), [])
    
    def test_get_connections_from(self):
        """出力からの接続の取得のテスト"""
        osc_component = StructureComponent("oscillator", "osc", {"type": "sine", "frequency": 440.0})
        filter_component = StructureComponent("filter", "filter", {"type": "lpf", "cutoff": 1000})
        reverb_component = StructureComponent("effect", "reverb", {"type": "reverb", "mix": 0.5})
        
        components = {
            "osc": osc_component,
            "filter": filter_component,
            "reverb": reverb_component
        }
        
        connections = [("osc", "filter"), ("osc", "reverb")]
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components, connections)
        
        self.assertEqual(structure.get_connections_from("osc"), ["filter", "reverb"])
        self.assertEqual(structure.get_connections_from("filter"), [])
    
    def test_to_json(self):
        """構造レベルのJSON変換のテスト"""
        osc_component = StructureComponent("oscillator", "main_osc", {"type": "sine", "frequency": 440.0})
        env_component = StructureComponent("envelope", "main_env", {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5})
        
        components = {
            "main_osc": osc_component,
            "main_env": env_component
        }
        
        connections = [("main_osc", "main_env")]
        source_parameters = ["frequency", "amplitude", "attack", "decay", "sustain", "release"]
        metadata = {"template_name": "basic_synth"}
        
        structure = StructureLevel(StructureType.SYNTH_DEF, components, connections, source_parameters, metadata)
        structure_json = structure.to_json()
        
        # JSONデコード
        structure_dict = json.loads(structure_json)
        
        self.assertEqual(structure_dict["structure_type"], "SYNTH_DEF")
        self.assertEqual(structure_dict["connections"], connections)
        self.assertEqual(structure_dict["source_parameters"], source_parameters)
        self.assertEqual(structure_dict["metadata"], metadata)
        self.assertEqual(structure_dict["components"]["main_osc"]["component_type"], "oscillator")
        self.assertEqual(structure_dict["components"]["main_env"]["component_type"], "envelope")
    
    def test_from_json(self):
        """構造レベルのJSONからの生成のテスト"""
        structure_json = """
        {
            "structure_type": "SYNTH_DEF",
            "components": {
                "main_osc": {
                    "component_type": "oscillator",
                    "name": "main_osc",
                    "value": {"type": "sine", "frequency": 440.0}
                },
                "main_env": {
                    "component_type": "envelope",
                    "name": "main_env",
                    "value": {"type": "adsr", "attack": 0.1, "decay": 0.2, "sustain": 0.7, "release": 0.5}
                }
            },
            "connections": [["main_osc", "main_env"]],
            "source_parameters": ["frequency", "amplitude", "attack", "decay", "sustain", "release"],
            "metadata": {"template_name": "basic_synth"}
        }
        """
        
        structure = StructureLevel.from_json(structure_json)
        
        self.assertEqual(structure.structure_type, StructureType.SYNTH_DEF)
        self.assertEqual(structure.connections, [["main_osc", "main_env"]])
        self.assertEqual(structure.source_parameters, ["frequency", "amplitude", "attack", "decay", "sustain", "release"])
        self.assertEqual(structure.metadata, {"template_name": "basic_synth"})
        self.assertEqual(structure.components["main_osc"].component_type, "oscillator")
        self.assertEqual(structure.components["main_env"].component_type, "envelope")


if __name__ == "__main__":
    unittest.main()
