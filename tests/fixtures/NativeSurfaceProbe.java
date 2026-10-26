// SPDX-License-Identifier: MIT
// Tests the real Pyjinn numeric boundary without connecting to Minecraft.
import java.nio.file.Files;
import java.nio.file.Path;
import org.pyjinn.interpreter.Script;
import org.pyjinn.parser.PyjinnParser;

public class NativeSurfaceProbe {
    public enum Heightmap { MOTION_BLOCKING_NO_LEAVES }

    public static class Heightmaps {
        public final Heightmap MOTION_BLOCKING_NO_LEAVES = Heightmap.MOTION_BLOCKING_NO_LEAVES;
    }

    public static class Level {
        public boolean hasChunk(int x, int z) {
            return x != 0 || z != 0;
        }

        public int getHeight(Heightmap type, int x, int z) {
            if (!hasChunk(x >> 4, z >> 4)) {
                throw new AssertionError("Queried an unloaded chunk");
            }
            return 64;
        }

        public int getMinY() { return -64; }
    }

    public static void main(String[] args) throws Exception {
        String source = Files.readString(Path.of(args[0]));
        Script script = new Script();
        Level level = new Level();
        script.set("level", level);
        script.set("Heightmap", new Heightmaps());
        script.compile(PyjinnParser.parse("shipped-surfaces.pyj", source)).exec();
        try {
            // Long inputs reproduce the Python bridge's numeric representation.
            long[][] origins = {{0, 0}, {-17, -1}, {29998990, -29998990}};
            for (long[] origin : origins) {
                Object result = script.getFunction("surfaces").call(
                    script.mainModule().globals(), origin[0], origin[1], 4L);
                StringBuilder expected = new StringBuilder();
                for (int dx = -4; dx <= 4; dx += 4) {
                    for (int dz = -4; dz <= 4; dz += 4) {
                        int x = (int) origin[0] + dx, z = (int) origin[1] + dz;
                        if (level.hasChunk(x >> 4, z >> 4)) {
                            if (expected.length() > 0) expected.append(';');
                            expected.append(x).append(",64,").append(z);
                        }
                    }
                }
                if (!expected.toString().equals(result)) {
                    throw new AssertionError("Surface output mismatch: " + result);
                }
            }
            System.out.println("Real Pyjinn surface lookup: PASS (3 coordinate cases)");
        } finally {
            script.exit();
        }
    }
}
