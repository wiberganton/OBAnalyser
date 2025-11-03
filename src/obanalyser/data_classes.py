from dataclasses import dataclass, asdict, field
from typing import List, Any, Mapping
import json


@dataclass
class FileStats:
    nmb_repetitions: int #n
    time: float #s
    energy: float #J
    nmb_spots: int #n
    line_length: float #m

@dataclass
class LayerInfo:
    layer_index: int
    layer_height: float #mm
    recoate_time: float #s
    files: List[FileStats]

    def get_layer_time(self):
        return sum(file.time * file.nmb_repetitions for file in self.files) + self.recoate_time
    def get_layer_energy(self):
        return sum(file.energy * file.nmb_repetitions for file in self.files)
    
@dataclass
class BuildInfo:
    layers: List[LayerInfo]
    start_temp: float #degress C
    start_heat: List[FileStats]

    def get_total_duration(self):
        total = 0.0
        for layer in self.layers:
            total += layer.get_layer_time()
        return total

    def to_json(self, file_path: str):
        """Serialize the BuildInfo object to a JSON file."""
        with open(file_path, "w") as f:
            json.dump(asdict(self), f, indent=4)

    @staticmethod
    def from_json(file_path: str) -> 'BuildInfo':
        """Deserialize a JSON file into a BuildInfo object."""
        with open(file_path, "r") as f:
            data = json.load(f)
        
        layers = [
            LayerInfo(
                layer_index=l['layer_index'],
                layer_height=l['layer_height'],
                recoate_time=l['recoate_time'],
                files=[FileStats(**fs) for fs in l['files']]
            )
            for l in data['layers']
        ]
        start_heat = [FileStats(**fs) for fs in data['start_heat']]
        return BuildInfo(
            layers=layers,
            start_temp=data['start_temp'],
            start_heat=start_heat
        )
@dataclass
class GeometryFileInfo:
    melt_area_mm2: float  # mm2
    total_area_mm2: float # mm2
    spot_size_um: float   # um

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "GeometryFileInfo":
        # Cast to float in case the JSON has ints/strings
        return GeometryFileInfo(
            melt_area_mm2=float(d["melt_area_mm2"]),
            total_area_mm2=float(d["total_area_mm2"]),
            spot_size_um=float(d["spot_size_um"]),
        )

@dataclass
class GeometryLayerInfo:
    layer_index: int
    melt_area_mm2: float  # mm2
    melt_portion: float   # %
    # Make files optional in JSON; write as [] when missing
    files: List[GeometryFileInfo] = field(default_factory=list)

    @staticmethod
    def from_dict(d: Mapping[str, Any]) -> "GeometryLayerInfo":
        files_raw = d.get("files") or []  # allow missing/null -> []
        files_parsed = [
            GeometryFileInfo.from_dict(f) if not isinstance(f, GeometryFileInfo) else f
            for f in files_raw
        ]
        return GeometryLayerInfo(
            layer_index=int(d["layer_index"]),
            melt_area_mm2=float(d["melt_area_mm2"]),
            melt_portion=float(d["melt_portion"]),
            files=files_parsed,
        )

@dataclass
class GeometryInfo:
    layers: List[GeometryLayerInfo]

    def to_json_file(self, filepath: str, indent: int = 4) -> None:
        """Write the GeometryInfo object to a JSON file."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=indent)

    @classmethod
    def from_json_file(cls, filepath: str) -> "GeometryInfo":
        """Read a GeometryInfo object from a JSON file.

        Accepts either:
          - {"layers": [ ...layer objects... ]}
          - [ ...layer objects... ]
        Each layer object may include "files": [ ...file objects... ] or omit it.
        If omitted or null, 'files' becomes an empty list.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            layers_data = data.get("layers", []) or []
        elif isinstance(data, list):
            layers_data = data
        else:
            raise ValueError("Invalid JSON format: expected object with 'layers' or a list.")

        layers = [GeometryLayerInfo.from_dict(item) for item in layers_data]
        return cls(layers=layers)