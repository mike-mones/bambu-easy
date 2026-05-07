# Hole Filling and Mesh Surgery

> Use this when removing screw holes, countersinks, embossed/recessed features, or unwanted through-holes from imported STL/3MF meshes without original CAD.

---

## Key principle

STL and most 3MF geometry is triangle mesh data, not editable CAD history. A hole is not a feature you can delete; it is just triangles forming a tunnel. Reliable repair usually means **mesh surgery**: remove the hole wall faces, trace boundary loops, and create new triangles that share vertices with the surrounding surface.

Boolean plugs often leave visible seams because the plug and wall meet as separate surfaces. Mesh surgery avoids that by welding the fill to the original boundary.

---

## When not to do mesh surgery

Prefer a simpler path when possible:
- If a parametric source exists, edit the CAD source instead.
- If the hole is hidden, a simple plug may be enough.
- If the surface is flat and cosmetic quality is unimportant, a flat patch is acceptable.
- If the model is high-risk or organic and the hole crosses complex detail, consider redesigning or finding a cleaner source model.

---

## Approaches to avoid

| Approach | Why it fails |
|---|---|
| Automatic "close holes" tools | Through-holes in watertight meshes are not open boundaries |
| Voxel resampling | Destroys detail and can explode memory use |
| Simple cylinder boolean plug | Creates a visible circular seam |
| Flat triangle fan on curved wall | Produces a flat scar |
| Large-radius blind probing | Hits unrelated nearby surfaces |
| Full-grid point clouds | Wasteful and memory-heavy |

---

## Proven workflow

### 1. Analyze the mesh

Load with `trimesh` and print bounds, vertex/face counts, watertight status, body count, and face density around the hole.

Use cross-sections to find circular features:

```python
section = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
paths = section.discrete if section is not None else []
```

Small circular paths are usually screw holes or countersinks. Sweep through the suspected wall depth to profile radius vs. depth.

### 2. Identify hole faces

Use face centroids and connectivity:
1. Build face adjacency.
2. Seed faces near the hole center in the plane perpendicular to the hole axis.
3. Flood-fill through connected faces while radius stays inside the maximum hole/countersink radius.
4. Stop at surrounding wall faces.
5. Print face count, radius range, and depth range.

Connectivity-aware flood fill is more reliable than deleting every face inside a radius because real triangulation rarely forms a perfect circle.

### 3. Remove faces and trace boundaries

After deleting hole faces:
1. Find edges belonging to exactly one remaining face.
2. Trace ordered boundary loops.
3. Expect two loops for a through-hole through a wall: front and back.
4. If loop count is wrong, adjust flood-fill limits before filling.

### 4. Fit the visible surface

For visible front faces, collect probe points on the surrounding original surface, away from countersink transitions and nearby model edges.

A useful quadratic form for a front/back wall is:

`y = a*x² + b*x + c*z + d`

Why quadratic: a plane cannot follow cylindrical or gently curved surfaces. Keep the fit simple, but verify residual error. If RMS residual is above ~0.02–0.05 mm on a cosmetic surface, probes are probably contaminated.

### 5. Fill with rings, not one fan

For the visible side:
1. Create 4+ concentric rings between boundary loop and center.
2. For each boundary vertex, compute correction from fitted surface to actual boundary vertex.
3. Blend correction to zero toward the center.
4. Triangulate rings as quads split into triangles.
5. Use the center vertex only for the innermost fan.

This gives a smooth patch that exactly matches the original boundary while avoiding a flat disk. For the hidden back side, a simple median-depth fan is often enough.

### 6. Validate

After rebuilding:
- `mesh.is_watertight` should be true when the original was watertight.
- Body count should remain expected.
- Normals should be fixed.
- Bounds should not change unexpectedly.
- Preview the patch under raking light if cosmetic.

---

## Useful trimesh snippets

```python
import numpy as np
import trimesh

mesh = trimesh.load(path, process=True)
print(mesh.bounds)
print(mesh.is_watertight)
print(len(mesh.faces), len(mesh.vertices))

edges = mesh.edges_sorted
unique, counts = np.unique(edges, axis=0, return_counts=True)
boundary_edges = unique[counts == 1]
```

Raycast from outside only when cross-sections are insufficient:

```python
def first_hit_y(mesh, x, z, from_negative=True):
    if from_negative:
        origin = np.array([[x, mesh.bounds[0][1] - 10.0, z]])
        direction = np.array([[0.0, 1.0, 0.0]])
    else:
        origin = np.array([[x, mesh.bounds[1][1] + 10.0, z]])
        direction = np.array([[0.0, -1.0, 0.0]])
    locs, _, _ = mesh.ray.intersects_location(origin, direction, multiple_hits=True)
    if len(locs) == 0:
        return None
    return float(locs[:, 1].min() if from_negative else locs[:, 1].max())
```

---

## Mesh format expectations

| Format | Editable feature history? | Notes |
|---|---|---|
| STL | No | Triangle soup only |
| 3MF | Usually no | Mesh plus settings/colors/metadata |
| STEP/IGES | Sometimes | B-rep CAD; may preserve useful solids |
| Native CAD | Yes | Best source if available |

Do not promise perfect restoration on organic surfaces. Classify complex mesh surgery as **INFERRED** until previewed and printed.

---

## Safety checklist

- Estimate memory before building adjacency on high-poly meshes.
- Avoid full voxel grids.
- Print progress for long repairs.
- Keep original file unchanged.
- Export a preview STL and compare before/after.
- If a cosmetic repair still shows a seam after two fundamentally different approaches, stop and propose a design alternative.
