// SPDX-License-Identifier: MIT
// Exercises our shipped snapshot function using the real Pyjinn interpreter.
import java.nio.file.Files;
import java.nio.file.Path;
import org.pyjinn.interpreter.Script;
import org.pyjinn.parser.PyjinnParser;

public class NativeTerrainProbe {
    public record Pos(int x, int y, int z) {}
    public static class Bounds {
        public final double minX=0,maxX=1,minZ=0,maxZ=1;
        public final double maxY;
        public Bounds(double top) { maxY=top; }
    }
    public record Shape(boolean empty, boolean full,double top) {
        public Shape(boolean empty,boolean full) { this(empty,full,0); }
        public boolean isEmpty() { return empty; }
        public java.util.List<Bounds> toAabbs() {
            return top>0?java.util.List.of(new Bounds(top)):java.util.List.of();
        }
    }
    public record Fluid(boolean empty) {
        public boolean isEmpty() { return empty; }
    }
    public static class ShapeHelpers {
        public static boolean isShapeFullBlock(Shape shape) { return shape.full(); }
    }
    public static class Context {
        public static Object of(Object player) { return player; }
    }
    public record State(String id, Shape shape, boolean wet) {
        public Shape getCollisionShape(Level level, Pos pos, Object context) { return shape; }
        public Fluid getFluidState() { return new Fluid(!wet); }
        @Override public String toString() { return "Block{"+id+"}"; }
    }
    public static class Level {
        public boolean closed;
        public boolean hasChunkAt(Pos pos) { return pos.x()<16; }
        public State getBlockState(Pos pos) {
            if(!hasChunkAt(pos)) throw new AssertionError("Read an unloaded chunk");
            if(pos.x()==3 && pos.y()==63)
                return new State("minecraft:farmland",new Shape(false,false,.9375),false);
            if(pos.x()==4 && pos.y()==63)
                return new State("minecraft:stone_slab",new Shape(false,false,.5),false);
            if(pos.y()==63) return new State("example:ceramic_tile",new Shape(false,true),false);
            if(pos.x()==0 && pos.y()==64)
                return new State("example:soft_growth",new Shape(true,false),false);
            if(pos.x()==1 && pos.y()==64)
                return new State("minecraft:oak_fence_gate",new Shape(!closed,false),false);
            if(pos.x()==2 && pos.y()==64)
                return new State("example:wet_growth",new Shape(true,false),true);
            return new State("minecraft:air",new Shape(true,false),false);
        }
    }
    public static class Client {
        public final Object player=new Object();
        public Level level=new Level();
    }
    private static Object call(Script script,String encoded) {
        return script.getFunction("probe").call(script.mainModule().globals(),encoded);
    }
    private static void expect(Object actual,String wanted) {
        if(!wanted.equals(actual)) throw new AssertionError("Expected "+wanted+", got "+actual);
    }
    public static void main(String[] args) throws Exception {
        Script script=new Script();
        Client client=new Client();
        script.set("mc",client);
        script.set("level",client.level);
        script.set("player",client.player);
        String header="BlockPos = JavaClass('NativeTerrainProbe$Pos')\n"
            +"Block = JavaClass('NativeTerrainProbe$ShapeHelpers')\n"
            +"Context = JavaClass('NativeTerrainProbe$Context')\n";
        script.compile(PyjinnParser.parse("shipped-terrain.pyj",
            header+Files.readString(Path.of(args[0])))).exec();
        try {
            expect(call(script,"-17,63,-1;0,64,0;1,64,0;2,64,0;16,64,0;3,63,0;4,63,0"),
                "6|Block{example:ceramic_tile}\n5|Block{example:soft_growth}\n"
                +"5|Block{minecraft:oak_fence_gate}\n4|Block{example:wet_growth}\n0|unknown\n"
                +"6|Block{minecraft:farmland}\n4|Block{minecraft:stone_slab}");
            client.level.closed=true;
            expect(call(script,"1,64,0"),"4|Block{minecraft:oak_fence_gate}");
            client.level=new Level();
            boolean rejected=false;
            try { call(script,"0,64,0"); }
            catch(RuntimeException exception) { rejected=true; }
            if(!rejected) throw new AssertionError("Stale world accepted");
            System.out.println("Real Pyjinn terrain lookup: PASS");
        } finally { script.exit(); }
    }
}
