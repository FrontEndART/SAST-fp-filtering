package my_app;

public class Main{
	public static int POPULATION = 0;
	public static final int SIDE_BUFFER_SIZE = 1024;
	public static int AVERAGE_AGE = 0;
	
	
	public static void main(String[] args) {
        Person p = new Person();
		String[] hobby = new String[]{"tailer"};
		p.setHobbies(hobby);
		Date personDate = p.getBirthDate();
		p.setBirthDate(personDate);
		System.out.println(p.getHobbies()[0] + p.getBirthDate().toString());
	}
}
