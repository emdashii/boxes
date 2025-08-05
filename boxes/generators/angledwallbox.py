# Copyright (C) 2013-2014 Florian Festi
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
from boxes import *


class AngledWallBox(Boxes):
    """Box with both ends cornered and walls angled outward forming a bowl shape"""

    ui_group = "Box"

    def __init__(self) -> None:
        Boxes.__init__(self)
        self.addSettingsArgs(edges.FingerJointSettings)
        self.buildArgParser(x=100.0, y=115.0, h=50, outside=True, bottom_edge="F")
        self.argparser.add_argument(
            "--n",  action="store", type=int, default=2,
            help="number of walls at one side (1+)")
        self.argparser.add_argument(
            "--top",  action="store", type=str, default="none",
            choices=["none", "angled hole", "angled lid", "angled lid2"],
            help="style of the top and lid")
        self.argparser.add_argument(
            "--wall_slope",  action="store", type=float, default=15.0,
            help="slope of walls in degrees (0=vertical, 90=horizontal)")

    def floor(self, x, y, n, edge='e', hole=None, move=None, callback=None, label=""):
        r, h, side  = self.regularPolygon(2*n+2, h=y/2.0)
        t = self.thickness

        if n % 2:
            lx = x - 2 * h + side
        else:
            lx = x - 2 * r + side

        edge = self.edges.get(edge, edge)

        tx = x + 2 * edge.spacing()
        ty = y + 2 * edge.spacing()

        if self.move(tx, ty, move, before=True):
            return

        self.moveTo((tx-lx)/2., edge.margin())

        if hole:
            with self.saved_context():
                hr, hh, hside  = self.regularPolygon(2*n+2, h=y/2.0-t)
                dx = side - hside
                hlx = lx - dx

                self.moveTo(dx/2.0, t+edge.spacing())
                for i, l in enumerate(([hlx] + ([hside] * n))* 2):
                    self.edge(l)
                    self.corner(360.0/(2*n + 2))

        for i, l in enumerate(([lx] + ([side] * n))* 2):
            self.cc(callback, i, 0, edge.startwidth() + self.burn)
            edge(l)
            self.edgeCorner(edge, edge, 360.0/(2*n + 2))

        self.move(tx, ty, move, label=label)

    def trapezoidalWall(self, bottom_width, top_width, height, edges="eeee", move=None, label=""):
        """Create a trapezoidal wall with different bottom and top widths"""

        # Calculate the angle for the sloped sides
        width_diff = (top_width - bottom_width) / 2
        slope_length = math.sqrt(height**2 + width_diff**2)

        edges = [self.edges.get(e, e) for e in edges]

        # Calculate total dimensions including edge spacing
        tw = max(bottom_width, top_width) + edges[1].spacing() + edges[3].spacing() + abs(width_diff)
        th = height + edges[0].spacing() + edges[2].spacing()

        if self.move(tw, th, move, before=True):
            return

        # Start drawing the trapezoid
        start_x = edges[3].margin() + (abs(width_diff) if top_width > bottom_width else 0)
        self.moveTo(start_x, edges[0].margin())

        # Bottom edge (connects to the floor)
        edges[0](bottom_width)

        # Right sloped edge
        angle = math.degrees(math.atan2(width_diff, height))
        self.corner(90 - angle)
        edges[1](slope_length)

        # Top edge - use actual top width so finger joints match the lid
        self.corner(90 + angle)
        edges[2](top_width)

        # Left sloped edge
        self.corner(90 + angle)
        edges[3](slope_length)

        # Close the shape
        self.corner(90 - angle)

        self.move(tw, th, move, label=label)

    def topFloor(self, x, y, n, edge='e', hole=None, move=None, callback=None, label=""):
        """Top floor adjusted for angled walls - using properly expanded polygon"""
        # Calculate the top dimensions based on wall slope
        slope_rad = math.radians(self.wall_slope)
        top_expansion = self.h * math.tan(slope_rad)

        # Calculate expanded dimensions for the polygon
        top_x = x + 2 * top_expansion
        top_y = y + 2 * top_expansion

        # Calculate polygon based on EXPANDED dimensions - this is key!
        r, h, side = self.regularPolygon(2*n+2, h=top_y/2.0)
        t = self.thickness

        if n % 2:
            lx = top_x - 2 * h + side
        else:
            lx = top_x - 2 * r + side

        edge = self.edges.get(edge, edge)

        tx = top_x + 2 * edge.spacing()
        ty = top_y + 2 * edge.spacing()

        if self.move(tx, ty, move, before=True):
            return

        # Calculate starting position
        self.moveTo((tx-lx)/2., edge.margin())

        if hole:
            with self.saved_context():
                # For the hole, calculate based on expanded dimensions minus thickness
                hr, hh, hside = self.regularPolygon(2*n+2, h=top_y/2.0-t)
                dx = side - hside
                hlx = lx - dx

                self.moveTo(dx/2.0, t+edge.spacing())
                for i, l in enumerate(([hlx] + ([hside] * n))* 2):
                    self.edge(l)
                    self.corner(360.0/(2*n + 2))

        # Draw the polygon with properly calculated edges for expanded dimensions
        for i, l in enumerate(([lx] + ([side] * n))* 2):
            self.cc(callback, i, 0, edge.startwidth() + self.burn)
            edge(l)  # Using correctly calculated edge lengths
            self.edgeCorner(edge, edge, 360.0/(2*n + 2))

        self.move(tx, ty, move, label=label)

    def render(self):

        x, y, h, n = self.x, self.y, self.h, self.n
        b = self.bottom_edge
        wall_slope = self.wall_slope

        if n < 1:
            n = self.n = 1

        if x < y:
            x, y = y, x

        if self.outside:
            x = self.adjustSize(x)
            y = self.adjustSize(y)
            if self.top == "none":
                h = self.adjustSize(h, False)
            elif "lid" in self.top and self.top != "angled lid":
                h = self.adjustSize(h) - self.thickness
            else:
                h = self.adjustSize(h)

        t = self.thickness

        r, hp, side = self.regularPolygon(2*n+2, h=y/2.0)

        if n % 2:
            lx = x - 2 * hp + side
        else:
            lx = x - 2 * r + side

        # Calculate angled wall dimensions
        slope_rad = math.radians(wall_slope)
        top_expansion = h * math.tan(slope_rad)

        # Calculate the expanded polygon dimensions to get correct edge lengths
        top_x = x + 2 * top_expansion
        top_y = y + 2 * top_expansion
        r_top, hp_top, side_top = self.regularPolygon(2*n+2, h=top_y/2.0)

        if n % 2:
            lx_top = top_x - 2 * hp_top + side_top
        else:
            lx_top = top_x - 2 * r_top + side_top

        fingerJointSettings = copy.deepcopy(self.edges["f"].settings)
        fingerJointSettings.setValues(self.thickness, angle=360./(2 * (n+1)))
        fingerJointSettings.edgeObjects(self, chars="gGH")

        with self.saved_context():
            if self.top != "none":
                # When we have a top, draw bottom first, then top pieces
                if b != "e":
                    self.floor(x, y, n, edge='f', move="right", label="Bottom")
                if self.top == "angled lid":
                    self.topFloor(x, y, n, edge='e', move="right", label="Lower Lid")
                    self.topFloor(x, y, n, edge='E', move="right", label="Upper Lid")
                elif self.top in ("angled hole", "angled lid2"):
                    self.topFloor(x, y, n, edge='F', move="right", hole=True, label="Top Rim and Lid")
                    if self.top == "angled lid2":
                        self.topFloor(x, y, n, edge='E', move="right", label="Upper Lid")

        # Only generate spacing calculation if we're making a top piece
        if self.top != "none":
            self.topFloor(x, y, n, edge='F', move="up only")

        fingers = self.top in ("angled lid2", "angled hole")

        # Start a new row for walls to prevent overlap
        self.ctx.save()

        cnt = 0
        for j in range(2):
            cnt += 1
            if j == 0 or n % 2:
                # Use the properly calculated top dimensions from expanded polygon
                self.trapezoidalWall(lx, lx_top, h,
                                   edges=b+"GfG" if fingers else b+"GeG",
                                   move="right", label=f"angled wall {cnt}")
            else:
                self.trapezoidalWall(lx, lx_top, h,
                                   edges=b+"gfg" if fingers else b+"geg",
                                   move="right", label=f"angled wall {cnt}")
            for i in range(n):
                cnt += 1
                # Use properly calculated side dimensions from expanded polygon
                if (i+j*((n+1)%2)) % 2: # reverse for second half if even n
                    self.trapezoidalWall(side, side_top, h,
                                       edges=b+"GfG" if fingers else b+"GeG",
                                       move="right", label=f"angled wall {cnt}")
                else:
                    self.trapezoidalWall(side, side_top, h,
                                       edges=b+"gfg" if fingers else b+"geg",
                                       move="right", label=f"angled wall {cnt}")

        self.ctx.restore()

        # When top is "none", draw the bottom piece after all the walls to avoid overlap
        if self.top == "none" and b != "e":
            # Move to a new row for the bottom
            self.move(0, h + 20, "up only")  # Move up to clear the walls
            self.floor(x, y, n, edge='f', move="right", label="Bottom")