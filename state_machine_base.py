
# Empty prototype state class
class State:
    def __init__(self) -> None:
        pass
    
    
    async def on_enter(self) -> None:
        pass
    
    
    async def on_exit(self) -> None:
        pass
    
    
    async def step(self) -> None:
        pass
    
    
class StateMachine:
    def __init__(self) -> None:
        self.current_state: State = None
        self.prev_state: State = None
        
        
    def run(self) -> None:
        if self.current_state == self.prev_state:
            self.current_state.step()
            return
        
        self.prev_state.on_exit()
        self.current_state.on_enter()
        self.prev_state = self.current_state
        
        
    def set_state(self, state: State):
        self.current_state = state