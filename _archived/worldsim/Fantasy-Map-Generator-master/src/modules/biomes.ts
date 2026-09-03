import { mean, range } from "d3";
import { rn } from "../utils";

declare global {
  var Biomes: BiomesModule;
}

class BiomesModule {
  private MIN_LAND_HEIGHT = 20;

  getDefault() {
    const name: string[] = [
      "Marine",
      "Hot desert",
      "Cold desert",
      "Savanna",
      "Grassland",
      "Tropical seasonal forest",
      "Temperate deciduous forest",
      "Tropical rainforest",
      "Temperate rainforest",
      "Taiga",
      "Tundra",
      "Glacier",
      "Wetland",
      "Chaos (Reality Spike)",
      "Coastal Shelf",
      "Abyssal Trench",
      "Kelp Forests",
      "Thermal Vents"
    ];

    const color: string[] = [
      "#466eab",
      "#fbe79f",
      "#b5b887",
      "#d2d082",
      "#c8d68f",
      "#b6d95d",
      "#29bc56",
      "#7dcb35",
      "#409c43",
      "#4b6b32",
      "#96784b",
      "#d5e7eb",
      "#0b9131",
      "#a855f7", // Chaos purple
      "#3b82f6", // Coastal Shelf
      "#1e3a8a", // Abyssal Trench
      "#065f46", // Kelp Forests
      "#991b1b"  // Thermal Vents
    ];
    const habitability: number[] = [0, 4, 10, 22, 30, 50, 100, 80, 90, 12, 4, 0, 12, 0, 50, 5, 80, 10]; // Marine biomes now have subaquatic habitability
    const iconsDensity: number[] = [0, 3, 2, 120, 120, 120, 120, 150, 150, 100, 5, 0, 250, 100, 0, 0, 0, 0];
    const icons: Array<{ [key: string]: number }> = [
      {},
      { dune: 3, cactus: 6, deadTree: 1 },
      { dune: 9, deadTree: 1 },
      { acacia: 1, grass: 9 },
      { grass: 1 },
      { acacia: 8, palm: 1 },
      { deciduous: 1 },
      { acacia: 5, palm: 3, deciduous: 1, swamp: 1 },
      { deciduous: 6, swamp: 1 },
      { conifer: 1 },
      { grass: 1 },
      {},
      { swamp: 1 },
      { deadTree: 10 }, // Chaos
      {}, // Coastal
      {}, // Abyssal
      {}, // Kelp
      {}  // Thermal Vents
    ];
    const cost: number[] = [10, 200, 150, 60, 50, 70, 70, 80, 90, 200, 1000, 5000, 150, 9000, 50, 200, 80, 500]; // biome movement cost
    const biomesMatrix: Uint8Array[] = [
      // hot ↔ cold [>19°C; <-4°C]; dry ↕ wet
      new Uint8Array([1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 10]),
      new Uint8Array([3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 9, 9, 9, 9, 10, 10, 10]),
      new Uint8Array([5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 9, 9, 9, 9, 9, 10, 10, 10]),
      new Uint8Array([5, 6, 6, 6, 6, 6, 6, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 10, 10, 10]),
      new Uint8Array([7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 10, 10])
    ];

    // PHASE 5 HACK: define underwater biomes matrix based on depth (height) and temperature
    // Depth: shallow (h:15-19), mid (h:5-14), deep (h:0-4)
    // using biomes 13: Ocean, 14: Coastal Shelf, 15: Coral Reef, 16: Kelp, 17: Vents
    const underwaterBiomesMatrix: Uint8Array[] = [
      // deep (h:0-4)
      new Uint8Array([17, 17, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13]),
      // mid (h:5-14)
      new Uint8Array([16, 16, 16, 16, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13, 13]),
      // shallow (h:15-19)
      new Uint8Array([15, 15, 15, 15, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14, 14])
    ];

    // parse icons weighted array into a simple array
    const parsedIcons: string[][] = [];
    for (let i = 0; i < icons.length; i++) {
      const parsed: string[] = [];
      for (const icon in icons[i]) {
        for (let j = 0; j < icons[i][icon]; j++) {
          parsed.push(icon);
        }
      }
      parsedIcons[i] = parsed;
    }

    return {
      i: range(0, name.length),
      name,
      color,
      biomesMatrix,
      underwaterBiomesMatrix,
      habitability,
      iconsDensity,
      icons: parsedIcons,
      cost
    };
  }

  define() {
    TIME && console.time("defineBiomes");

    const { fl: flux, r: riverIds, h: heights, c: neighbors, g: gridReference } = pack.cells;
    const { temp, prec } = grid.cells;
    pack.cells.biome = new Uint8Array(pack.cells.i.length); // biomes array

    const calculateMoisture = (cellId: number) => {
      let moisture = prec[gridReference[cellId]];
      if (riverIds[cellId]) moisture += Math.max(flux[cellId] / 10, 2);

      const moistAround = neighbors[cellId]
        .filter((neibCellId: number) => heights[neibCellId] >= this.MIN_LAND_HEIGHT)
        .map((c: number) => prec[gridReference[c]])
        .concat([moisture]);
      return rn(4 + (mean(moistAround) as number));
    };

    for (let cellId = 0; cellId < heights.length; cellId++) {
      const height = heights[cellId];
      const moisture = height < this.MIN_LAND_HEIGHT ? 0 : calculateMoisture(cellId);
      const temperature = temp[gridReference[cellId]];
      pack.cells.biome[cellId] = this.getId(moisture, temperature, height, Boolean(riverIds[cellId]));
    }

    TIME && console.timeEnd("defineBiomes");
  }

  getId(moisture: number, temperature: number, height: number, hasRiver: boolean) {
    if (height < 20) {
      // PHASE 5 HACK: Subaquatic mapping based on underwater biomes matrix
      const depthBand = height < 5 ? 0 : height < 15 ? 1 : 2; // 0: deep, 1: mid, 2: shallow
      const temperatureBand = Math.min(Math.max(20 - temperature, 0), 25); // [0-25]
      return biomesData.underwaterBiomesMatrix[depthBand][temperatureBand];
    }
    if (temperature < -5) return 11; // too cold: permafrost biome
    if (temperature >= 25 && !hasRiver && moisture < 8) return 1; // too hot and dry: hot desert biome
    if (this.isWetland(moisture, temperature, height)) return 12; // too wet: wetland biome

    // in other cases use biome matrix
    const moistureBand = Math.min((moisture / 5) | 0, 4); // [0-4]
    const temperatureBand = Math.min(Math.max(20 - temperature, 0), 25); // [0-25]
    return biomesData.biomesMatrix[moistureBand][temperatureBand];
  }

  private isWetland(moisture: number, temperature: number, height: number) {
    if (temperature <= -2) return false; // too cold
    if (moisture > 40 && height < 25) return true; // near coast
    if (moisture > 24 && height > 24 && height < 60) return true; // off coast
    return false;
  }
}

window.Biomes = new BiomesModule();
