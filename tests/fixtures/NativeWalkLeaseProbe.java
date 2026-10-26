// SPDX-License-Identifier: MIT
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import org.pyjinn.interpreter.Script;
import org.pyjinn.parser.PyjinnParser;

public class NativeWalkLeaseProbe {
    public record Timer(Script.Function callback, int millis, Object generation) {}
    public static class Api {
        public boolean forward, jump, sneak;
        public int starts;
        public double x, z;
        public String menu;
        public final ArrayList<Timer> timers = new ArrayList<>();
        public void player_press_forward(boolean down) {
            if (down && !forward) starts++;
            forward = down;
        }
        public void player_press_jump(boolean down) { jump = down; }
        public void player_press_sneak(boolean down) { sneak = down; }
        public String screen_name() { return menu; }
        public double[] player_position() { return new double[] {x, 64, z}; }
        public boolean remove_event_listener(Number id) { return true; }
        public int set_timeout(Script.Function callback, int millis, Object generation) {
            timers.add(new Timer(callback, millis, generation));
            return timers.size();
        }
    }

    private static Object call(Script script, String name, Object... args) {
        return script.getFunction(name).call(script.mainModule().globals(), args);
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        Script script = new Script();
        Api api = new Api();
        script.set("ms", api);
        script.compile(PyjinnParser.parse("shipped-walk-lease.pyj",
            Files.readString(Path.of(args[0])))).exec();
        try {
            require(((Number) call(script,"drive",600L,false,false,0.0,0.0,5.0)).intValue()==1,
                    "First drive rejected");
            Timer first = api.timers.getLast();
            call(script,"drive",700L,false,false,0.0,0.0,5.0);
            Timer last = api.timers.getLast();
            first.callback().call(script.mainModule().globals(),first.generation());
            require(api.forward && api.starts==1,"Stale timer interrupted continuous movement");
            last.callback().call(script.mainModule().globals(),last.generation());
            require(!api.forward,"Expiry failed to brake");
            api.x=4.9;
            require(((Number) call(script,"drive",600L,false,false,0.0,0.0,5.0)).intValue()==0,
                    "Drive accepted an exhausted runway after a delayed Python call");
            require(!api.forward,"Exhausted runway restarted forward");
            api.x=2;
            call(script,"drive",600L,false,false,0.0,0.0,5.0);
            require(api.timers.getLast().millis()<=336,"Already traveled distance was ignored");
            api.menu="Chat";
            call(script,"tick",(Object)null);
            require(!api.forward && !api.sneak,"Menu failed to release movement");
            require(((Number)call(script,"drive",600L,false)).intValue()==-1,
                    "An aborted controller restarted");
            call(script,"close");
            System.out.println("Real Pyjinn walk lease: PASS");
        } finally { script.exit(); }
    }
}
