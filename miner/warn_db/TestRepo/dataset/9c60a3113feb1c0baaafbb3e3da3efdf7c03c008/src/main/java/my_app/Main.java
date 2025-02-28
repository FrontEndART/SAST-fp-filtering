package my_app;

public class Main{
	public static int SIDE_BUFFER_SIZE = 1024;
	
	
	public static void main(String[] args) {
        Person p = new Person();
		String[] hobby = new String[]{"tailer"};
		p.setHobbies(hobby);
		System.out.println(p.getHobbies()[0]);
	}
}
